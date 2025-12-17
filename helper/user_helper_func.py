import os,json

DATA_FILE="data/users.json"

class Userhelper_functions:
    
    def load_users(self):
        if not os.path.exists(DATA_FILE):
            return []
        with open(DATA_FILE,"r") as f:
            return json.load(f)
        
    def save_user(self,users):
        self.users=users
        with open(DATA_FILE,"w") as f:
            json.dump(users,f,indent=4)
            
    
        