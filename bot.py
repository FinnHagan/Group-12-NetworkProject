#Connect to miniircd python miniircd --ipv6 --debug

import socket, time

#Initialising variables
PORT = 6667
HOST = "::1" #fc00:1337::17/96 is the host we will use, ::1 is for testing purposes
CHANNEL = "#hello"
NICK = "BOT"

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
        connect = s.recv(2048).decode("UTF-8") #Recieves the bots nickname
        print("BOT information has been successfully sent to the server." + connect)      
    except:
        print("BOT information was unable to be sent to the server, please try again.")
        exit()

#Function to join the channel
def join():
    #Sends the join command to the server
    try:
        print("Attempting to join channel... ")
        #Join the channel
        s.send(bytes("JOIN "+ CHANNEL + "\r\n", "UTF-8"))
        s.send(bytes("PRIVMSG "+ CHANNEL + " :Hello! I am a (ro)bot!\r\n", "UTF-8"))
        join = s.recv(2048).decode("UTF-8")
        print("Successfully joined: " + join)
    except:
        print("Unable to join channel: ")
        exit()

#Function to PING back so that it doesn't ping timeout
def ping_pong(message):
    s.send(bytes("PONG :" + message + "\r\n", "UTF-8"))

#Splitting the message
def message_split(message):
    message = message.split(" ")
    return message

#Main function
def main():
    connect()
    join()

    #While loop to keep the server from timing out
    while True:
        message = s.recv(2048).decode("UTF-8")
        print(message)
        message = message_split(message)
        
        if message[0] == "PING":
            ping_pong(message[0])
                        
#Calls the main function to start the program
main()