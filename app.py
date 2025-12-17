from flask import Flask,request,url_for,redirect,render_template
from helper.user_helper_func import Userhelper_functions
from datetime import datetime,timedelta
import json

app=Flask(__name__)

user_helper=Userhelper_functions()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add-user",methods=["POST","GET"])
def add_user():
    if request.method=="POST":
        name=request.form["name"]
        phone=request.form["phone"]
        
        users=user_helper.load_users()
        
        #check if user already exists
        for u in users:
           if u["phone"]==phone:
               return "USER ALREADY EXIST"
           
        users.append({
            "name":name,
            "phone":phone,
            "balance":100,
            "last_transaction":"no transaction yet",
            "transaction_history":[]
        })
        
        user_helper.save_user(users)
        return redirect(url_for("index"))
    
    return render_template("add_user.html")

@app.route("/search",methods=["POST","GET"])
def search_user():
    if request.method=="POST":
        query=request.form["query"]
        users = user_helper.load_users()
    
        for u in users:
            if u["name"].lower().strip() == query.lower().strip() or u["phone"].strip() == query.strip():
                return render_template("search_user.html", user=u)
    
        return render_template("search_user.html",user=None,message="user not found")
    
    return render_template("search_user.html",user=None)

@app.route("/view-users",methods=["GET"])
def view_users():
    users=user_helper.load_users()
    return render_template("view_user.html",users=users)

@app.route("/update-balance/<phone>",methods=["POST","GET"])
def update_balance(phone):
    users=user_helper.load_users()
    
    now=datetime.now()
    
    user=next((u for u in users if u["phone"]==phone),None)
    
    if not user:
        return "User not found"
    
    with open("data/customer_of_month.json","r") as file:
        month_data=json.load(file)
        customer_of_month_phone=month_data.get("phone","")
        
        is_customer_of_month=(phone==customer_of_month_phone)
            
    if request.method=="POST":
        amount=float(request.form["amount"])
        action=request.form["action"]
        
        discount_code = request.form.get("discount_code", "").strip().upper()
        
        base_amount=amount
        
        if is_customer_of_month and action=="deduct":
            discount=base_amount*0.10
            base_amount-=discount
            
        if now.weekday()>=5 and action=="deduct":
            discount=base_amount*0.30
            base_amount-=discount
            
        if discount_code == "OFF30%" and action == "deduct":
            discount = base_amount * 0.30
            base_amount -= discount
            
        
        # ---------- ADD BALANCE ----------
        if action=="add":
            user["balance"]+=base_amount
            transaction_type="deposite"
            applied_gst=0
            
            final_amount=base_amount
        
        # ---------- DEDUCT BALANCE ----------   
        elif action=="deduct":
            applied_gst=amount*0.18
            final_amount=base_amount+applied_gst
            if user["balance"]<final_amount:
                return "No sufficient Balance in your account"
            user["balance"]-=final_amount
            transaction_type="withdraw"
        
        # ---------- Save Transaction ---------  
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user["last_transaction"]=timestamp
        
        user["transaction_history"].append({
            "type":transaction_type,
            "base_amount":round(base_amount,2),
            "gst":round(applied_gst,2),
            "final_amount":round(final_amount,2),
            "time":timestamp,
            "balance_after":round(user["balance"],2),
            "discount_code": discount_code
        })
               
        user_helper.save_user(users) 
        return redirect(url_for("search_user"))   
    
    return render_template("update_balance.html",user=user)
    
@app.route("/transactions/<phone>",methods=["POST","GET"])
def view_transactions(phone):
    users=user_helper.load_users()
    user=next((u for u in users if u["phone"]==phone),None)
    
    if not user:
        return "no user found"
    
    history=user["transaction_history"]
    
    total_spent=sum(t["amount"] for t in history if t["type"].lower()=="withdraw")
    
    # Find highest spending (largest withdraw)
    withdraws=[t for t in history if t["type"].lower()=="withdraw"]
    
    if withdraws:
        lowest_spending=min(withdraws,key=lambda x: x["amount"])
        highest_spending=max(withdraws,key=lambda x: x["amount"])
    else:
        lowest_spending=None
        highest_spending=None
    
    return render_template(
        "transaction_history.html",
        user=user,
        show_history=True,
        total_spent=total_spent,
        lowest_spending=lowest_spending,
        highest_spending=highest_spending
    )
    
@app.route("/customer-of-month")
def customer_of_month():
    users=user_helper.load_users()
    
    now=datetime.now()
    current_month=now.month
    current_year=now.year
    
    user_stats=[]
    
    for u in users:
        history=u.get("transaction_history",[])
        
        # Filter transactions for only THIS month
        monthly_transaction=[]
        
        # convert string → datetime
        for t in history:
            t_date=datetime.strptime(t["time"],"%Y-%m-%d %H:%M:%S")
            
            if t_date.year==current_year and t_date.month==current_month:
                monthly_transaction.append(t)
            
        total_spending=sum(t["amount"] for t in monthly_transaction if t["type"].lower()=="withdraw")
        visit_count=len(monthly_transaction)
        
        user_stats.append({
            "user":u,
            "total_spending":total_spending,
            "visit_count":visit_count
        })
        
    if not user_stats:
        return render_template("customer_of_month.html",user=None)
    
    best_user=sorted(user_stats,key=lambda x:(x["total_spending"],x["visit_count"]),reverse=True)[0]
    
    # Store the customer of the month
    with open("data/customer_of_month.json","w") as file:
        json.dump({"phone":best_user["user"]["phone"]},file)

    
    return render_template(
        "customer_of_month.html",
        user=best_user["user"],
        total_spending=best_user["total_spending"],
        visit_count=best_user["visit_count"]
    )
    
    
    
    
if __name__=="__main__":
    app.run(debug=True,port=7000)
    
