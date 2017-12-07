# -*- coding: utf-8 -*-
"""
Created on Wed Nov 22 10:28:41 2017

@author: Juha Hirvonen

sanapeli.py

Python game where the player forms as many Finnish words from random letters 
as (s)he can within a certain time. Needs a text file that contains all legal
Finnish words. Here a file "sanalista.txt" is used. It is txt file made from
the xml file included in the package "kotus-sanalista-v1.zip" available in
http://kaino.kotus.fi/sanat/nykysuomi/
For the high scores the program will generate a txt file "high_score.txt" in
the same folder this file is.


"""
#from IPython import get_ipython
#get_ipython().magic('reset -sf')

try:
    import tkinter as tk
except ImportError:
    import Tkinter as tk
from random import sample
from re import compile, I
from itertools import permutations
from os.path import isfile


# The class for the game
class wordGame():
    
    def __init__(self, root):
        
        self.master = root
        root.title('Sanaskaba - Sanaseppojen näytön paikka!')
        root.geometry('600x520')
        
        # Defining the points that are given from the different word lenghts 
        # and the number of letters based on the dict
        self.point_data = {3:1, 4:2, 5:4, 6:7, 7:12}
        self.min_word_length = sorted(self.point_data.keys())[0]
        self.n_letters = sorted(self.point_data.keys())[-1]
        
        # Defining the configuration files
        self.high_score_file = 'high_score.txt'
        self.word_list_file = 'sanalista.txt'
        
        # Initializing the values
        self.running = 0 # Showing if the game is on
        self.min_words_doable = 10 # Minimum number of words that can be...
        self.time_limit = 60 # in s #  ...generated from the given letters
        self.text_entry = tk.StringVar()
        self.game_letters = tk.StringVar()
        self.points_text = tk.StringVar()
        self.time_text = tk.StringVar()
        self.points_text_begin = 'Pisteet: '
        self.time_text_begin = 'Aika: '
        self.messages_text = tk.StringVar()
        self.accepted_answers = tk.StringVar()
        self.missed_answers = tk.StringVar()
        self.end_text = tk.StringVar()
        self.high_score_text = tk.StringVar()
       
        # Game rules printed in the beginning
        rulesText = ('Muodosta vähintään ' + str(self.min_word_length) + 
                     '-kirjaimisia sanoja annettujen kirjaimien avulla. '
                     'Aikaa on ' + str(self.time_limit) + ' sekuntia. '
                     'Sanojen tulee olla perusmuodossa. Saat pisteitä '
                     'sanojen pituuden mukaan seuraavasti: \n \n')
        for ind in range(self.min_word_length, self.n_letters + 1):
            if ind in self.point_data:
                if self.point_data[ind] == 1:
                    rulesText += str(ind) + ' kirjainta - 1 piste \n'
                else:
                    rulesText += (str(ind) + ' kirjainta - ' + 
                                  str(self.point_data[ind]) + ' pistettä \n')
                    
        # The label showing the letters from which the words have to be formed
        lettersLabel = tk.Label(root, textvariable = self.game_letters, 
                                font = ('Helvetica', 16, 'bold'))
        lettersLabel.grid(row = 1, column = 1)
        
        # The edit text field where the player gives the input
        self.entryField = tk.Entry(root, textvariable = self.text_entry)
        self.entryField.grid(row = 2, column = 1)
        self.entryField.config(state = 'disabled')
        
        # The label showing the time
        timeLabel = tk.Label(root, textvariable = self.time_text)
        timeLabel.grid(row = 0, column = 2, sticky = tk.E)
        
        # The label showing the points
        pointsLabel = tk.Label(root, textvariable = self.points_text)
        pointsLabel.grid(row = 0, column = 0, sticky = tk.W)
        
        # The label showing the messages to the player based on their actions
        self.messagesLabel = tk.Label(root, textvariable = self.messages_text)
        self.messagesLabel.grid(row = 3, column = 1, sticky = 'N')
        
        # The label showing the accepted words entered by the player
        acceptedLabel = tk.Label(root, textvariable = self.accepted_answers)
        acceptedLabel.grid(row = 3, column = 0, sticky = 'NW', rowspan = 2)
        
        # The label showing the answers missed in the end of the game
        missedMessage = tk.Message(root, textvariable = self.missed_answers)
        missedMessage.config(justify = tk.CENTER, width = 100)
        missedMessage.grid(row = 3, column = 2, sticky = 'NE', rowspan = 2)
        
        # The label showing the rules of the game
        rulesMessage = tk.Message(root, text = rulesText)
        rulesMessage.config(justify = tk.CENTER)
        rulesMessage.grid(row = 5, column = 1)
        
        # The new game button
        newgameButton = tk.Button(master = root, text = 'Uusi peli', 
                                  command = self.initialize_game)
        newgameButton.grid(row = 4, column = 1)
        
        # The label showing the game over message
        endtextMessage = tk.Message(root, textvariable = self.end_text, 
                                font = ('Helvetica', 20, 'bold'))
        endtextMessage.config(justify = tk.CENTER, width = 200)
        endtextMessage.grid(row = 3, column = 1)
        
        # The label showing the best score
        highscoreLabel = tk.Label(root, textvariable = self.high_score_text)
        highscoreLabel.grid(row = 1, column = 0, sticky = 'W')
        
        # Binding pressing Enter to the enter_word function
        root.bind('<Return>', self.enter_word)
        
        # Defining the look
        root.rowconfigure(3, {'minsize': 250})
        root.columnconfigure(0, {'minsize': 150})
        root.columnconfigure(1, {'minsize': 150})
        root.columnconfigure(2, {'minsize': 150})
        
        if not(isfile(self.word_list_file)):
            self.end_text.set('Virhe! Sanatiedostoa: "' + 
                              self.word_list_file + '" ei löydy.')
            newgameButton.config(state = 'disabled')
            
        
    
    # The function, which initializes a new game when the new game button is 
    # pressed
    def initialize_game(self):
        
        # If new game has been started before the finishing the previous,
        # the old timer needs to be switched off
        if self.running:
            self.master.after_cancel(self.timer)
            self.running = 0
        
        # Intializing the game parameters
        self.points = 0
        self.time = self.time_limit + 1
        self.valid_words = [] 
        self.answers = []
        
        # Generating a letter pool from where the letters are picked (as in 
        # Scrabble)
        letter_pool = (10*'a' + 10*'i' + 9*'n' + 9*'t' + 8*'e' + 7*'s' + 5*'k' 
                       + 5*'l' + 5*'o' + 5*u'ä' + 4*'u' + 3*'m' + 2*'h' + 2*'j'  
                       + 2*'p' + 2*'u' + 2*'y'+ 2*'v' +u'döbgfc')
        
        # Picking the letters randomly for the game until enough words can be 
        # made from them
        while len(self.valid_words) < self.min_words_doable:
            
            # Picking the letters randomly
            letters = sample(letter_pool, self.n_letters)
            letters = ''.join(letters)
            
            # Finding all the Finnish words that contain only the given letters 
            # (same letters may have been used multiple times here).
            # The final list of the valid words is composed using this list as 
            # a reference
            pattern = (']{' + str(self.min_word_length) + ',' 
                        + str(self.n_letters+1) + '}$')
            composed = compile('[' + letters + pattern, I).match
            with open(self.word_list_file, encoding = 'utf-8') as inf:
                words = set(word.rstrip('\n') for word in inf 
                            if composed(word))
                    
            # Finding all the valid Finnish words possible to form from the 
            # given letters with length in the given range
            self.valid_words = []
            for wordlen in range(self.min_word_length, self.n_letters + 1):
                perms = permutations(letters, wordlen)
                for trial in perms:
                    trial = ''.join(trial)
                    if trial in words and not(trial in self.valid_words):
                        self.valid_words.append(trial)
        
        # Reading the high score                 
        if (isfile(self.high_score_file)):
            scoreFile = open(self.high_score_file)
            self.high_score = int(scoreFile.read())
            scoreFile.close()
        else:
            self.high_score = 0
        
        # Initializing the texts seen in the game window and enabling 
        # the text entries
        self.game_letters.set(letters.upper())
        self.points_text.set(self.points_text_begin + str(self.points))
        self.messages_text.set('')
        self.accepted_answers.set('Löydetyt: \n')
        self.missed_answers.set('')
        self.end_text.set('')
        self.entryField.config(state = 'normal')
        self.text_entry.set('')
        self.high_score_text.set('Paras tulos: ' + 
                                 str(self.high_score))
        self.time_text.set(self.time_text_begin + str(self.time))
        
        # Starting the timer
        self.update_time()
        self.running = 1
        
        # The cursor to the text entry
        self.entryField.focus()

    
    # The function, which operates the clock
    def update_time(self):
        self.time = self.time - 1
        self.time_text.set(self.time_text_begin + str(self.time))
        
        # If time has finished, printing the message telling that, the final 
        # points and a list of the worlds the player did not type
        if self.time < 0.1: # Account for rounding errors
            self.running = 0
            self.time_text.set(self.time_text_begin + '0')
            self.end_game()
        else:
            self.timer = self.master.after(1000, self.update_time)
            
            
    # The function, which reads the user input, checks if it is legal and 
    # gives the points accordingly
    def enter_word(self, event):
        # Reading the entry and clearing the edit text field
        if self.running:
        
            word_given = self.text_entry.get().lower()
            self.text_entry.set('')
            
            # If the given word is legal, it is printed below and the points 
            # are updated accordingly. Also a message telling the acceptance is
            # shown. Otherwise, a message telling the rejectance is shown.
            if not(word_given in self.valid_words):
                self.messages_text.set('Sana "' + word_given + 
                                       '" ei ole laillinen.')
                self.messagesLabel['fg'] = 'red'
            elif word_given in self.answers:
                self.messages_text.set('Sana "' + word_given + '" on jo ' + 
                                       u'syötetty.')
                self.messagesLabel['fg'] = 'orange3' 
            else:
                self.answers.append(word_given)
                word_length = len(word_given) 
                new_points = self.point_data[word_length]
                self.points += new_points
                self.points_text.set(self.points_text_begin + str(self.points))
                if new_points == 1:
                    message = (u'Sana "' + word_given + u'" hyväksytty. '
                               '+1 piste.')
                else:
                    message = (u'Sana "' + word_given + u'" hyväksytty. +' + 
                               str(new_points) + u' pistettä.')
                self.messages_text.set(message) 
                self.messagesLabel['fg'] = 'green4'
                answers_string = self.accepted_answers.get()
                self.accepted_answers.set(answers_string + '\n' + word_given)

    
    # The function, which is launched when the game ends
    def end_game(self):
        # Disabling the entry field
        self.entryField.config(state = 'disabled')
        self.master.after_cancel(self.timer)
        self.running = 0
        
        end_message = 'Aika loppui. Pisteesi: ' + str(self.points) + ' '
        
        # Checking if a new record was made
        if self.points > self.high_score:
            end_message += 'Uusi ennätys!'
            scoreFile = open(self.high_score_file, "w")
            scoreFile.write(str(self.points))
            scoreFile.close()
        
        # Showing the game over message and the words the player did not find
        self.end_text.set(end_message)
        words_unused = set(self.valid_words) - set(self.answers)
        words_unused = sorted(words_unused, key=len)
        words_unused_str = u'Löytämättä jäivät: \n \n'
        for word in words_unused:
            words_unused_str += word + ' '
        self.missed_answers.set(words_unused_str)


# The main function
if __name__ == "__main__":
    
    master = tk.Tk()
    sanapeli = wordGame(master)
    master.mainloop()

