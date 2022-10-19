import socket, time, argparse, random, datetime
#Connect to miniircd python miniircd --ipv6 --debug

#Initialising variables
PORT = 6667
HOST = "::1" #fc00:1337::17/96 is the host we will use, ::1 is for testing purposes
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
PORT = args.port
NICK = args.name
CHANNEL = args.channel
#Initialising the socket
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)

#Function to connect to the server
def connect():

    #Tries to connect to the sever
    try:
        print("BOT is trying to connect to the server...")
        #Connecting to the server
        s.connect((HOST, PORT))
        #Alerts the user what HOST and PORT the BOT is connecting to
        print (f"Connecting at {HOST}/{PORT}")

    #If the BOT cannot to connect to the server
    except:
        print("BOT failed to connect to the server, attempting to reconnect...")
        time.sleep(5)
        #Try to connect again
        try:
            s.connect((HOST, PORT))
        #If failed again, stop trying to reconnect
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
    #Sends the join command to the server
    try:
        print("Attempting to join channel... ")
        #Join the channel
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

#Function to display the users in the channel
def display_users(msg):
    for i in range(5, len(msg)):
        if i == 5:
            userList.append(msg[i][1:])
            continue
        userList.append(msg[i])
    print("Current users in the channel: ")
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
    origin= msg[0][1:].split("!",1)[0]
    message = msg[3] #Get the message
    destination = msg[2] #What channel or user the message is directed to

    if len(origin) < 17:

        #Lets us know that the message is either a private message or a channel message
        if destination.lower() == CHANNEL.lower():
            #If 
            if message.find("!hello") != -1:
                greeting = datetime.datetime.now().strftime('%d-%m-%y %H:%M')
                send_message("Hello " + origin + " it is currently " + greeting + " ", destination)

            if message.find("!slap") != -1:
                randomSlap = get_random_user()
                send_message("slaps " + randomSlap + " around a bit with a large trout", destination)

        #Lets us know it is a private message        
        if destination.lower() == NICK.lower():
            #Hence respond with a random fact
            if message != -1:
                fact = get_random_fact()
                send_message(fact, origin)

#Function to handle separate commands
def handle_commands(msg):
    # print(msg)
    try:
        #If the message is a PING, then PONG back
        if msg[0] == "PING":
            ping_pong(msg[0])
        #If a PRIVMSG, then process the message   
        elif msg[1] == "PRIVMSG":
            process_message(msg)
        #If a 353, then display the users in the channel
        elif msg[1] == "353":
            display_users(msg)
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
    
    #Add in handling of arguments into this loop too.

                        
#Calls the main function to start the program
main()