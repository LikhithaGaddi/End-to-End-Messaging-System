import socket             
import sys
from getpass import getpass
from contextlib import closing
import threading 
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from random import randint
import hashlib

MSG_SIZE = 8192
NUMBER_OF_SERVERS = 3
P = 2409254109293510934796826672457339113288246933600376490751081491620048007627
G = 57497496415798496487974961489794797496526549798416415749
# a = randint(256479958749921167964964789456314,2147483678798454189795262645941965798796526548747)
GROUP_KEY={}
SIGN_IN = False

def error(msg):
    print(msg)
    exit(0)

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    return [s,s.getsockname()[1]]  
    

def connect_to_peer(ip,port,mesg,isfile):
    soc_id = socket.socket()
    if (soc_id.connect_ex((ip, port)))==0:
        if isfile:
            send_msg(soc_id, "file")
        else:
            send_msg(soc_id,"msg")
            key = deffe_Hellman(soc_id,ROLL_NO)
            encrypt_and_send(soc_id,mesg,key)
        soc_id.close()
     

def connect_to_server(server_no):
    for i in range(NUMBER_OF_SERVERS):
        cli_sd = socket.socket()
        file1=sys.argv[1]+str(server_no)+".txt"
        try:
            f = open(file1, 'r')
            lines = f.readlines() 
            if len(lines)>1:
                server_ip =lines[0].strip()
                server_port =int(lines[1].strip())
            else:
                error("Provide IP addr and Port number in the file")  
        except FileNotFoundError:
            error("file not found")

        # try to connect to the server
        if (cli_sd.connect_ex((server_ip, server_port)))==0:
            print("Connected to server"+str(server_no))
            return cli_sd
        else:
            server_no=(server_no+1)%3
    
    error("Connection failed: Server is not available")    

#consistant hashing to know which server we must connect to#
#generate a random no. between 1 to 2
def random1():
    return randint(0,1)
def get_server_number():
    #return 2
    x = -1
    y = random1()
    while(x==-1):
        x = random1()
        x = 2*x-(y&1)
    # print("random num:",x)
    return x


#calculate key
def deffe_Hellman_server(s, roll_number):
    a = randint(256479958749921167964964789456314,2147483678798454189795262645941965798796526548747)
    a = (str(a)[0:24] + roll_number)
    a = (hashlib.sha256(a.encode()))
    a = int(a.hexdigest(),16)
    x = int(pow(G, a, P))
    send_data = padding_msg(str(x))
    received_data=s.recv(MSG_SIZE).decode('utf-8')
    s.sendall(str.encode(send_data))
    ga = int(received_data)
    key = int(pow(ga, a, P))
    return str(key)[0:24]

def recieve_file(sock_id,roll_number,cipher):
    mesg = decryption(sock_id.recv(MSG_SIZE),cipher,True)
    filename,username= mesg.split(":")
    if filename == "no file":
        return
    filename = roll_number + filename
    sock_id.sendall(encryption("dummy",cipher,True))
    with open(filename, 'wb') as f:
        # print('file opened')
        while True:
            # print('receiving data...')
            data = sock_id.recv(MSG_SIZE)
            sock_id.sendall("dummy".encode())
            data = decryption(data, cipher,False)
            msg = str(data).split("'")
            if "done" in msg[1].strip():
                f.close()
                print('Received file from '+ username+": "+ filename+"\n> ",end="")
                return
            
            f.write(data)
## Client is listening to connections of other peers##
def server_func(args):
    server_sd,server_port=args
    server_sd.listen(5)
    while True:
        cli_sd, addr = server_sd.accept() 
        msg=cli_sd.recv(MSG_SIZE).decode('utf-8')
        cli_sd.send("dummy".encode())
        key="NONE"
        if("msg" in msg):
            if(msg=="msg"):
                key=deffe_Hellman_server(cli_sd,ROLL_NO)
            else:
                group= msg.split(':')[1]
                key=GROUP_KEY[group]    
            msg=cli_sd.recv(MSG_SIZE)
            cipher = DES3.new(key, DES3.MODE_ECB)
            msg=decryption(msg, cipher,True).split(':')
            print("Message from",msg[1],":",msg[0],"\n> ",end="")
        else:
            if(msg=="file"):
                key=deffe_Hellman_server(cli_sd,ROLL_NO)
            else:
                group= msg.split(':')[1]
                key=GROUP_KEY[group]
            cipher = DES3.new(key, DES3.MODE_ECB)
            recieve_file(cli_sd,ROLL_NO,cipher)
        
        cli_sd.close()
        
def break_message(msg):
    lst=msg.split()
    msg=(' ').join(lst[2:])
    return [lst[1],msg]
    

def encrypt_and_send(soc_id,mesg,key):
    cipher = DES3.new(key, DES3.MODE_ECB)
    mesg = encryption(mesg,cipher,True)
    soc_id.sendall(mesg)
  
class thread(threading.Thread):  
    def __init__(self, thread_name, thread_ID):  
        threading.Thread.__init__(self)  
        self.thread_name = thread_name  
        self.thread_ID = thread_ID  
  
    # helper function to execute the threads 
    def run(self): 
        if(str(self.thread_name)=="server"):
            server_func(self.thread_ID)
        elif(str(self.thread_name)=="group"):
            #user;mesg;group;flag
            lst=str(self.thread_ID).split(';')
            group_thread(lst[1],lst[0],lst[2],lst[3])
def send_msg(cli_sd,msg):
    cli_sd.send(msg.encode()) 
    msg = cli_sd.recv(MSG_SIZE).decode('utf-8')
    return msg

def deffe_Hellman(s, roll_number):
    # roll_number should be of 10
    a = randint(256479958749921167964964789456314,2147483678798454189795262645941965798796526548747)
    a = (str(a)[0:24] + str(roll_number))
    a = (hashlib.sha256(a.encode()))
    a = int(a.hexdigest(),16)
    x = int(pow(G, a, P))
    send_data = padding_msg(str(x))    
    s.sendall(str.encode(send_data))
    msg = s.recv(MSG_SIZE)
    received_data = msg.decode('utf-8')
    ga = int(received_data)
    key = int(pow(ga, a, P))
    return str(key)[0:24]

def padding_file(msg):
    xs = bytearray(msg)
    while len(xs) % 8 != 0:
        xs.append(0)
    return bytes(xs)

def padding_msg(msg):
    while len(msg) % 8 != 0:
        msg += " "
    return msg

def encryption(msg,cipher,is_msg):
    if is_msg:
        msg = padding_msg(msg)
    else:
        msg = padding_file(msg)
    return cipher.encrypt(msg)

def decryption(msg, cipher,isString):
    decrypted = cipher.decrypt(msg)
    if isString:
        return str(decrypted).split("'")[1].strip()
    return decrypted

def group_thread(mesg,user,group,isfile):
    ip,port=user.split(':')
    port = int(port)
    soc_id = socket.socket()
    key = GROUP_KEY[group]
    if (soc_id.connect_ex((ip, port)))==0:
        if eval(isfile):
            send_msg(soc_id,"file_group:"+group)
            cipher = DES3.new(key, DES3.MODE_ECB)
            send_file(mesg,soc_id,cipher)
        else:
            send_msg(soc_id,"msg_group:"+group)
            encrypt_and_send(soc_id,mesg,key)
            # encrypt_and_send(soc_id,mesg)
        soc_id.close()

def send_to_group(mesg,users,group,isfile):
    key=GROUP_KEY[group]
    for user in users:
        # info=user+";"+mesg+";"+group+";"+isfile
        ip,port=user.split(':')
        port = int(port)
        soc_id = socket.socket()
        if (soc_id.connect_ex((ip, port)))==0:
            if isfile:
                send_msg(soc_id,"file_group:"+group)
                cipher = DES3.new(key, DES3.MODE_ECB)
                send_file(mesg,soc_id,cipher)
            else:
                send_msg(soc_id,"msg_group:"+group)
                encrypt_and_send(soc_id,mesg,key)
                # encrypt_and_send(soc_id,mesg)
            soc_id.close()

def send_file(mesg, sock_id,cipher):
    filename,username=mesg.split(":")
    try:
        f = open(filename, 'rb')
    except FileNotFoundError:
        sock_id.send(encryption("no file:username", cipher, True))
        print("file doesn't exist :(")
        return
    sock_id.send(encryption(mesg, cipher, True))
    d = sock_id.recv(1024)  
    l = f.read(MSG_SIZE)
    while (l):
        sock_id.send(encryption(l, cipher, False))
        sock_id.recv(MSG_SIZE)
        l = f.read(MSG_SIZE)
        if not l:
            break
    sock_id.send(encryption("done", cipher, True))
    sock_id.recv(MSG_SIZE)
    f.close()

if len(sys.argv)<2:
    error("Wrong number of arguments")
 
server_no = get_server_number()
cli_sd=connect_to_server(server_no) 
cli_ip="127.0.0.1"
#Get a free port number and socket id of that port
lst1= find_free_port()
thread1=thread("server",lst1)
cli_port=lst1[1]
thread1.daemon=True
thread1.start()
print("Please Sign UP/Sign In")
while True:
    msg=input("> ").strip()
        
        ## Sign Up##
    if msg.lower()=="sign up" or msg.lower()=="signup":
        if SIGN_IN:
            print("already signed in!")
            continue

        msg=send_msg(cli_sd,"sign up")
        lst=[]
        lst.append(input("Enter Name: ").strip())
        lst.append(input("Enter Roll No: ").strip())
        lst.append(input("Enter Username: ").strip())
        lst.append(getpass("Password: ").strip())
        password=input("Confirm Password: ").strip()
        while password != lst[3]:
            print("Password doen't match")
            lst[3]=getpass("Password: ").strip()
            password=input("Confirm Password: ").strip()
        lst.append(cli_ip)
        lst.append(cli_port)
            # initialize(lst[2],lst[3],lst[1]) 
        USERNAME=lst[2]
        PASSWORD=lst[3]
        ROLL_NO=lst[1]
        msg = (':'.join(map(str, lst)))  
        reply=send_msg(cli_sd,msg)
        if reply=="exist":
            print("username is not available. Try someother username")
        else:
            SIGN_IN=True
            print("Sign UP successfull.")
            
    elif msg.lower()=="sign in" or msg.lower()=="signin":
        if SIGN_IN:
            print("already signed in!")
            continue

        send_msg(cli_sd,"sign in")
        lst=[]
        lst.append(input("Enter Username: ").strip())
        lst.append(getpass("Password: ").strip())
        lst.append(cli_ip)
        lst.append(str(cli_port))
        msg = ':'.join(lst)
        msg=send_msg(cli_sd,msg)
        
        if ("success" in msg):
            SIGN_IN=True
            lst1=msg.split(":")
            USERNAME=lst[0]
            PASSWORD=lst[1]
            ROLL_NO=lst1[1]
            userGroups = lst1[2:]
            # print('you were in groups')
            for userGroup in userGroups:
                groupname, groupkey = userGroup.split(',')
                GROUP_KEY[groupname] = groupkey
                # print('gname',groupname,'gkey',groupkey)
            print("Successfully loggen in")
        elif msg=="sign_in":
            print("User with that credentials is already logged in")
            continue
        else:
            print("Incorrect username or password. Try again")
            print("Sign In/ Sign Up")
            continue    
    elif "send" in msg.lower():
        if not SIGN_IN:
            print("you are not signed in. New user=>signup otherwise signin")
            continue
        
        if "grp" in msg.lower():
            send_msg(cli_sd,"send group")
            groups,mesg=break_message(msg)
            cli_sd.send((USERNAME+':'+groups).encode())
            groups=groups.split(',')
            # print('sending to',groups)
            flag=False
            if "file" in msg.lower():
                mesg=mesg.split()[1].strip()
                flag= True       
            distinct_lst=[]
            for group in groups:
                reply=cli_sd.recv(MSG_SIZE).decode('utf-8')
                if(reply=="no group"):
                    print(group+" doesn't exist\n")
                elif reply=="not in group":
                    print("you don't belong to the group "+group)
                elif reply =="None":
                    cli_sd.send("dummy".encode())
                    continue
                else:
                    lst_users=reply.split(',')
                    
                    info=";"+mesg+':'+USERNAME+";"+group+";" +str(flag)
                    thread_lst=[]
                    for user in lst_users:
                        t=thread("group",user+info)
                        thread_lst.append(t)
                    for t in thread_lst:
                        t.start()
                    for t in thread_lst:
                        t.join()
                     
                cli_sd.send("dummy".encode())
                 
        else:
            send_msg(cli_sd,"send msg")
            username,mesg= break_message(msg)
            reply=send_msg(cli_sd,username)
            if reply == "no user":
                    print("No user with that username")
                    continue
            ip,port,name = reply.split(':')
            soc_id = socket.socket()
            if (soc_id.connect_ex((ip, int(port))))!=0:
                continue
            
            if "file" in msg.lower():
                # print("##send file to the user##")
                mesg=mesg.split()[1].strip()
                send_msg(soc_id, "file")
                key = deffe_Hellman(soc_id,ROLL_NO)
                cipher = DES3.new(key, DES3.MODE_ECB)
                send_file(mesg+":"+USERNAME,soc_id,cipher)
                # print("done")
            else:
                               
                send_msg(soc_id,"msg")
                key = deffe_Hellman(soc_id,ROLL_NO)
                mesg=mesg+":"+USERNAME
                encrypt_and_send(soc_id,mesg,key)
            soc_id.close()
                
    elif "create" in msg.lower():
        if not SIGN_IN:
            print("you are not signed in. New user=>signup otherwise signin")
            continue
        send_msg(cli_sd, "create group")
        group_name = msg.split(" ")[1]
        lst = [group_name, USERNAME]
        msg = ':'.join(lst)
        reply = send_msg(cli_sd, msg)
        if reply=="exist":
            print("Group is already created.")
        else:
            GROUP_KEY[group_name] = reply.split(":")[1]
            print("Group created successfully.")

    elif "join" in msg.lower():
        if not SIGN_IN:
            print("you are not signed in. New user=>signup otherwise signin")
            continue        
        group_names = msg.split(" ")[1]
        for group_name in group_names.split(","):
            send_msg(cli_sd, "join group")
            lst = [group_name, USERNAME]
            msg = ':'.join(lst)
            reply = send_msg(cli_sd, msg)
            if reply == "group not exist":
                print("Group with name "+ group_name+" doesn't exists")
            elif reply=="exist":
                print("Already member of the group "+ group_name)
            else:
                GROUP_KEY[group_name] = reply.split(":")[1]
                print("Joined group " + group_name + " successfully.")

    
    elif "list" in msg.lower():
        if not SIGN_IN:
            print("you are not signed in. New user=>signup otherwise signin")
            continue        
        send_msg(cli_sd, "list group")
        reply = send_msg(cli_sd, "dummy")
        group_details = reply.split(":")
        print("<group_name,number_of_participants>")
        for group in group_details:
            print(group)


    elif msg=="exit":
        send_msg(cli_sd,"exit")
        if not SIGN_IN:
            cli_sd.send("dummy".encode())
        else:
            cli_sd.send(USERNAME.encode())
        SIGN_IN=False
        break
        
cli_sd.close()
# thread1.kill() 
# thread1.join()   
# if __name__ == "__main__":
#     main()


# thread1.join() 

# close the connection  
    
      
