import socket
import sys
import threading
from random import randint

MSG_SIZE = 1024
NUMBER_OF_SERVERS = 3
UserName_Info ={} # dictionary map of username to his details (object) {user_name:user}   
GROUP_INFO={} #group name to group object {groupname:user}
# ACTIVE_USERS=[] # list of usernames
User_to_Group = {} # maps username=>[group1, group2, ... ]

class User:
    def __init__(self, name, roll_no, user_name,password,ip_addr,port):
        self.name = name
        self.roll_no = roll_no  
        self.user_name = user_name
        self.password = password
        self.ip_addr = ip_addr
        self.port = port
        self.sign_in=True
    def update_ip_port(self,ip_addr,port):
        self.ip_addr = ip_addr
        self.port = port

class Group:
    def __init__(self,key,user1):
        # print('user1', user1)
        self.users=[user1]
        self.key = key
    
    def join_group(self,user1):
        self.users.append(user1)
    
    def get_key(self):
        return self.key
    

class thread(threading.Thread):  
    def __init__(self, thread_name, thread_ID):  
        threading.Thread.__init__(self)  
        self.thread_name = thread_name  
        self.thread_ID = thread_ID  
        # helper function to execute the threads 
    def run(self):
        if self.thread_name == "handle_connection":
            handle_connection(self.thread_ID)
        elif self.thread_name == "start_server":
            start_server(self.thread_ID)  

def error(msg):
    print(msg)
    exit(0)

def get_ip_and_port(file1):
    try:
        f = open(file1, 'r')
        lines = f.readlines() 
        if len(lines)>1:
            ip =lines[0].strip()
            port =int(lines[1].strip())
            return [ip,port]
        else:
            error("Provide IP addr and Port number in the file")
    except FileNotFoundError:
        error("file not found")    

def start_server(file1):
    server_ip,server_port=get_ip_and_port(file1)
    server_sd = socket.socket()
    server_sd.bind(('', server_port))  
    # server_sd.bind('',)
    server_sd.listen(5)
    while True:
        cli_sd, addr = server_sd.accept()      
        # print ('Got connection from', addr , 'to ', server_port)
        thread1=thread("handle_connection",cli_sd) 
        thread1.start() 
    server_sd.close()

def create_group(lst):
    user1=UserName_Info[lst[1]]
    a = str(randint(256479958749921167964964789456314, 2147483678798454189795262645941965798))
    key = a[0:24]
    group1 = Group(key,user1)
    GROUP_INFO[lst[0]] = group1
    return key

def maintain_user_groupList_info(username, groupname):
    if(username not in User_to_Group.keys()):
        User_to_Group[username] = []
    User_to_Group[username].append([groupname, GROUP_INFO[groupname].get_key])

# After connecting to the client. communication between client and server#
def handle_connection(cli_sd):    
    while True:  
        msg=cli_sd.recv(MSG_SIZE).decode('utf-8')
        if(msg.lower() == "sign up"):
            cli_sd.send('dummy'.encode())
            msg=cli_sd.recv(MSG_SIZE).decode('utf-8')
            lst = msg.split(":")
            if lst[2] in UserName_Info:
                cli_sd.send('exist'.encode())
            else:
                user1 = User(lst[0],lst[1],lst[2],lst[3],lst[4],lst[5])
                UserName_Info[lst[2]]=user1
                cli_sd.send('success'.encode())
        
        elif msg.lower()=="sign in":
            cli_sd.send('dummy'.encode())
            msg=cli_sd.recv(MSG_SIZE).decode('utf-8')
            lst = msg.split(':')
            if lst[0] not in UserName_Info:
                cli_sd.send('no user'.encode())
            else:
                user1 = UserName_Info[lst[0]]
                if user1.sign_in:
                    cli_sd.send('sign_in'.encode())
                elif user1.password != lst[1]:
                    cli_sd.send('Invalid'.encode())
                else:
                    user1.sign_in=True
                    user1.update_ip_port(lst[2],lst[3])
                    msg='success:'+user1.roll_no
                    #add [groupName, groupKey] of this user
                    if(lst[0] in User_to_Group.keys()):
                        for val in User_to_Group[lst[0]]:
                            msg = msg+':'+val[0]+','+str(val[1])
                    cli_sd.send(msg.encode())

        elif(msg=="send msg"):
            cli_sd.send('dummy'.encode())
            msg=cli_sd.recv(MSG_SIZE).decode('utf-8')
            if msg not in UserName_Info:
                cli_sd.send('no user'.encode())
            else:
                user1 = UserName_Info[msg]
                if user1.sign_in==False:
                    msg="no user"
                else:
                    msg=user1.ip_addr+":"+user1.port+":"+user1.name
                cli_sd.send(msg.encode())

        elif msg == "create group":
            cli_sd.send('dummy'.encode())
            msg = cli_sd.recv(MSG_SIZE).decode('utf-8')
            lst = msg.split(":")
            if lst[0] in GROUP_INFO:
                cli_sd.send('exist'.encode())
            else:
                key=create_group(lst)
                maintain_user_groupList_info(lst[1], lst[0])    #adding to User_to_Group dict username=>[list of groups]
                msg='success:'+key
                cli_sd.send(msg.encode())

        elif msg == "join group":
            cli_sd.send('dummy'.encode())
            msg = cli_sd.recv(MSG_SIZE).decode('utf-8')
            lst = msg.split(":")
            if lst[0] not in GROUP_INFO:
                key = create_group(lst)
                maintain_user_groupList_info(lst[1], lst[0])    #adding to User_to_Group dict username=>[list of groups]
                msg='success:'+key
                cli_sd.send(msg.encode())
                # cli_sd.send('group not exist'.encode())
            elif UserName_Info[lst[1]] in GROUP_INFO[lst[0]].users: #if user do not exist, that case need to be handeled
                cli_sd.send('exist'.encode())
            else:
                group1 = GROUP_INFO[lst[0]]
                key = group1.key
                group1.join_group(UserName_Info[lst[1]])
                GROUP_INFO[lst[0]] = group1
                maintain_user_groupList_info(lst[1], lst[0])  #adding to User_to_Group dict username=>[list of groups]
                msg='success:'+key
                cli_sd.send(msg.encode())
                
        elif msg == "list group":
            cli_sd.send('dummy'.encode())
            msg = cli_sd.recv(MSG_SIZE).decode('utf-8')
            lst = []
            for group in GROUP_INFO:
                lst.append(group + "," + str(len(GROUP_INFO[group].users)))
            cli_sd.send(":".join(lst).encode())


        
        elif(msg=="send group"):
            cli_sd.send('dummy'.encode())
            username,groups=cli_sd.recv(MSG_SIZE).decode('utf-8').split(':')
            groups=groups.split(',')
            
            for group in groups:
                msg="None"
                if group not in GROUP_INFO:
                    msg="no group"
                else:
                    user1=UserName_Info[username]
                    lst=GROUP_INFO[group].users
                    if user1.name not in [user.name for user in lst]:
                        msg="not in group"
                    else:
                        #lst.remove(user1)
                        lst=[str(x.ip_addr)+':'+str(x.port) for x in lst if x is not user1 and x.sign_in]
                        if len(lst)>0:
                            msg=(',').join(map(str,lst))  
                cli_sd.send(msg.encode())
                cli_sd.recv(MSG_SIZE).decode('utf-8')
                    

        elif msg=="exit":
            cli_sd.send('dummy'.encode())
            msg=cli_sd.recv(MSG_SIZE).decode('utf-8') #here msg contains username to be signed off
            if msg in UserName_Info:
                user1=UserName_Info[msg]
                user1.sign_in=False
            break

        
                
        # print (msg)


if len(sys.argv)!=2:
    error("Wrong number of arguments")

for i in range(NUMBER_OF_SERVERS):
    file1= sys.argv[1]+str(i)+".txt" #server0.txt
    t=thread("start_server",file1) 
    # t.daemon=True
    t.start()



# thread1.join()
# start_server(file1)  
