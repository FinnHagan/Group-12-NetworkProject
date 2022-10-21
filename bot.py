import socket, time, argparse, random, datetime
#Initialising variables
PORT = 6667
HOST = "fc00:1337::17"
CHANNEL = "#test"
NICK = "BOT"
userList = []
file = "facts.txt"

#Command line arguments for user to enter their own details
parser = argparse.ArgumentParser(description="Details for IRC bot")
parser.add_argument("--host", "--h", help= "Please enter your server's IP address", required = False, default = HOST)
parser.add_argument("--port", "--p", help= "Please enter your server's port number", required = False, default = PORT)
parser.add_argument("--name", "--n", help= "Please enter the nickname of the bot", required = False, default = NICK)
parser.add_argument("--channel", "--c", help= "Please enter the channel you would like to join", required = False, default = CHANNEL)
args = parser.parse_args()
HOST = args.host
PORT = int(args.port) #Needs converted to int as # can't be processed in the terminal
NICK = args.name
CHANNEL = args.channel

#Initialising the socket
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

#Function to connect to the server
def connect():
    try:
        print("BOT is trying to connect to the server...")
        s.connect((HOST, PORT))
        #Alerts the user what HOST and PORT the BOT is connecting to
        print (f"Connecting at {HOST}/{PORT}")

    #If the BOT cannot to connect to the server
    except:
        print("BOT failed to connect to the server, attempting to reconnect...")
        time.sleep(5)
        try:
            s.connect((HOST, PORT))
        except:
            print("BOT cannot connect to the server, disconnecting...")
            exit()    
    try:
        #Sending client information to the server
        s.send(bytes("USER "+ NICK + " "+ NICK +" "+ NICK + " :python\r\n", "UTF-8"))
        s.send(bytes("NICK "+ NICK + "\r\n", "UTF-8")) #Sets the bots nick name
        print("BOT information has been successfully sent to the server.")      
    except:
        print("BOT information was unable to be sent to the server, please try again.")
        exit()

#Function to join the channel
def join(chan):
    try:
        print("Attempting to join channel... ")
        #Sending join information to the server
        s.send(bytes("JOIN "+ chan + "\r\n", "UTF-8"))
        print("Successfully joined channel.")
    except:
        print("Unable to join channel: ")
        exit()

#Function to PING back so that it doesn't ping timeout
def ping_pong(message):
    s.send(bytes("PONG :" + message + "\r\n", "UTF-8"))

#Splitting the message for ping pong
def message_split(message):
    message = message.split(" ")
    return message

#Function to display the users in the channel and store their information
def display_users(msg):
    for i in range(5, len(msg)):
        if i == 5:
            userList.append(msg[i][1:])
            continue
        userList.append(msg[i])
    print("Current users in the channel: ")
    userList.remove(NICK)
    print(userList)
    return userList

#If a user joins the channel, add them to the user list
def update_users_joining(msg):
    user = msg[0][1:].split("!",1)[0]
    if user not in userList:
        userList.remove(NICK)
        userList.append(user)
        print(userList)

#If a user leaves the channel, remove them from the user list
def update_users_leaving(msg):
    user = msg[0][1:].split("!",1)[0]
    if user in userList:
        userList.remove(NICK)
        userList.remove(user)
        print(userList)

#Get random fact from text file
def get_random_fact():
    with open('facts.txt', 'r') as f:
        lines = f.read().splitlines()
        return random.choice(lines)

#Send a message to the desired person
def send_message(message, target):
    s.send(bytes("PRIVMSG " + target + " :" + message + "\r\n", "UTF-8"))

#Get a random user from the channel
def get_random_user():
    user = random.choice(userList)
    return user

#Process messages as per the their string format
def process_message(msg):
    origin= msg[0][1:].split("!",1)[0] #Finds the origin of the message
    message = msg[3] #Gets the message
    destination = msg[2] #What channel or user the message is directed to

    #Lets us know that the message is either a private message or a channel message
    if destination.lower() == CHANNEL.lower():
        
        #Responds appropriately to the hello command 
        if message.find("!hello") != -1:
            greeting = datetime.datetime.now().strftime('%d-%m-%y %H:%M')
            send_message("Hello " + origin + " it is currently " + greeting + " ", destination)
        
        #Responds appropriately to the slap command
        if message.find("!slap") != -1:
            #Slaps a random user which is not the bot or themselves
            randomSlap = origin
            slapped = randomSlap
            while slapped == randomSlap:
                randomSlap = get_random_user()
            send_message("Slap " + randomSlap + " around the face with a large trout", destination)
                        
    #Lets us know it is a private message        
    if destination.lower() == NICK.lower():
        #Hence respond with a random fact
        if message != -1:
            fact = get_random_fact()
            send_message(fact, origin)

#Function to handle separate commands
def handle_commands(msg):
    try:
        if msg[0] == "PING":
            ping_pong(msg[0])
        #If a PRIVMSG, then process the message   
        elif msg[1] == "PRIVMSG":
            process_message(msg)
        #If a 353, then display the users in the channel
        elif msg[1] == "353":
            display_users(msg)
        #If a 433, then the BOT nickname is already in use
        elif msg[1] == "433":
            print("BOT nickname is being used, please try again using command line arguments.")
            exit()
        elif msg[1] == "JOIN":
            update_users_joining(msg)
        elif msg[1] == "QUIT":
            update_users_leaving(msg)
    except:
        return
        
#Main function
def main():  
  connect()
  join(CHANNEL)
  #Infinite while loop to keep the bot running
  while True:
    #Parses the seperate commands
    info = s.recv(2048).decode("UTF-8")
    messages = info.split("\r\n")
    for msg in messages:   
        print(msg)
        msg = message_split(msg)
        handle_commands(msg)
main()