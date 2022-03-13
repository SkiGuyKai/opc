import tkinter as tk
from tkinter import messagebox
from tkmacosx import Button
from tkinter import ttk

import pandas as pd
import numpy as np
import yfinance as yf
from functools import partial
from contract import Contract

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure

HEIGHT = 800
WIDTH = 1200

# Pantone's Color of the Year 2022
# "The Star of the Show" Palette
BLACK_BG = '#29282D'
VOLCANIC_BG = '#625C60'
LL_1 = '#796762'
LL_2 = '#8E7961'
LL_3 = '#AEA392'
HL_1 = '#F0EDE8'
HL_2 = '#D8D4D0'
VERI_PERI = '#6667AB'

root = tk.Tk()
root.title('Option Profit Calculator by Ski.Guy.Kai')
root.geometry(f"{WIDTH}x{HEIGHT}")
# Prevent resizing
root.resizable(False, False)

# Create main user interface frame
left_frame = tk.Frame(root, bg=VOLCANIC_BG).place(relwidth=0.5, relheight=1)

# Create frame for display
right_frame = tk.Frame(root, bg=BLACK_BG).place(relwidth=0.5, relheight=1, x=WIDTH * 0.5)

# Create frame for cart
cart_frame = tk.Frame(root, bg=HL_1).place(relwidth=0.5, relheight=0.2, y=640)

# Global variables
# Ones not listed here: raw, calls, puts
symbol = tk.StringVar()
oExp = tk.StringVar()
numStrikes = tk.IntVar()
strikes_numList = [5, 5, 10, 15]

# Cart widgets & more
cart = []
typeLabels = []
dirLabels = []
quantityLabels = []
costEntries = []
removeButtons = []

# Option chain widgets
strikeLabels = []
callButtons = [[], []] # 0 is bid, 1 is ask
putButtons = [[], []]
changeLabels = [[], []] # 0 is call, 1 is put

# Create commands
def caps(): # Capitalizes text in entry box
    symbol.set(symbol.get().upper())

def opc_help():
    help_box = messagebox.showinfo(title='Help', message="To get started, enter an exchange-traded asset's symbol in the empty box. Pressing 'return' will retrieve the expiration periods, selecting one will display the option chain. Simply click on the bid/ask to add the contract to your cart.")

def set_numStrikes(n):
    numStrikes.set(n)

def get_exp(): # Get tuple of expiration and set StringVar
    global raw
    raw = yf.Ticker(symbol_entry.get()) # Asset is an object
    oExp.set(raw.options)

def get_data(): # Find and send expiration into the disp_data function
    idx = int(exp_list.curselection()[-1]) # Get expiration from listbox
    exp = raw.options[idx]
    clean(exp)

def clean(exp): # Cleans the data before displaying
    global calls
    calls = raw.option_chain(exp).calls
    global puts
    puts = raw.option_chain(exp).puts

    allStrikes = []
    # Add all strikes to list
    for strike in calls['strike']:
        allStrikes.append(strike)

    for strike in puts['strike']:
        allStrikes.append(strike)

    # Sort and remove duplicates
    allStrikes = list(set(allStrikes))

    # Identify strikes not in calls and puts
    dropStrikes = []
    for strike in allStrikes:
        if strike not in list(calls['strike']):
            dropStrikes.append(strike)

        if strike not in list(puts['strike']):
            dropStrikes.append(strike)

    # Drop rows in dataframes that don't contain dual-listed strikes
    allIdxs = calls.index.tolist()
    idxs = []
    dropIdxs = []
    # This populates a list with tuples as (index, strike)
    for idx in allIdxs:
        idxs.append((idx, calls.iloc[idx, 2]))

    # This identifies the indexer of strikes to be dropped
    for i in range(len(idxs)):
        for strike in dropStrikes:
            if strike == idxs[i][1]:
                dropIdxs.append(idxs[i][0])
    # Remove one-sided contracts
    calls.drop(dropIdxs, inplace=True)

    # Repeat the above code for puts
    allIdxs = puts.index.tolist()
    idxs = []
    dropIdxs = []
    for idx in allIdxs:
        idxs.append((idx, puts.iloc[idx, 2]))

    for i in range(len(idxs)):
        for strike in dropStrikes:
            if strike == idxs[i][1]:
                dropIdxs.append(idxs[i][0])

    puts.drop(dropIdxs, inplace=True)

    index = [i for i in range(len(calls.index))]

    calls.index = index
    puts.index = index

    # Now we can display the clean data
    disp_data()

def disp_data(): # Self-explanatory, will revisit to handle page overflow
    # Sacrifice all widgets in exchange for programming skills
    for widget in strikeLabels:
        widget.destroy()

    for t in zip(callButtons, putButtons, changeLabels): # Tuple of lists
        for l in t: # Each list in tuple
            for widget in l: # Each item in list
                widget.destroy()

    # This behemoth finds the index where ITM switches to OTM, then it sets
    # the starting range to this divider minus the desired number of strikes
    n = int(calls.index[calls['inTheMoney'] != calls['inTheMoney'].shift(1)][-1] - int(numStrikes.get()))

    # Make sure we start at a minimum index of 0
    if n < 0:
        n = 0

    # Iterative label and button creation for each contract
    for i in range(n, n + int(numStrikes.get()) * 2):
        y = i - n # y value for widget placement; must be different than n

        # Break loop when we hit the limit
        if i == calls.index[-1]:
            print(i, 'Index Limit!')
            break

        # Display call-side buttons and labels
        if calls.iloc[i, 11]: # Quick color logic for ITM/OTM
            BG = LL_3
        else:
            BG = HL_2

        changeLabels[0].append(tk.Label(left_frame, text=round(calls.iloc[i, 6], 2), bg=BG))
        changeLabels[0][-1].place(width=50, height=20, x=150, y=20 * (y + 2))

        callButtons[0].append(Button(left_frame, text=f'{calls.iloc[i, 4]}', command=partial(cartAdd, calls, 'call', 'sell', i), bg=BG, highlightbackground=BG))
        callButtons[0][-1].place(width=50, height=20, x=200, y=20 * (y + 2))

        callButtons[1].append(Button(left_frame, text=f'{calls.iloc[i, 5]}', command=partial(cartAdd, calls, 'call', 'buy', i), bg=BG, highlightbackground=BG))
        callButtons[1][-1].place(width=50, height=20, x=250, y=20 * (y + 2))

        # Display strikes
        strikeLabels.append(tk.Label(left_frame, text=calls.iloc[i, 2], bg=HL_1))
        strikeLabels[-1].place(width=50, height=20, x=300, y=20 * (y + 2))

        # Display put-side buttons and labels
        if puts.iloc[i, 11]:
            BG = LL_3
        else:
            BG = HL_2

        changeLabels[1].append(tk.Label(left_frame, text=round(puts.iloc[i, 6], 2), bg=BG))
        changeLabels[1][-1].place(width=50, height=20, x=450, y=20 * (y + 2))

        putButtons[0].append(Button(left_frame, text=f'{puts.iloc[i, 4]}', command=partial(cartAdd, puts, 'put', 'sell', i), bg=BG, highlightbackground=BG))
        putButtons[0][-1].place(width=50, height=20, x=350, y=20 * (y + 2))

        putButtons[1].append(Button(left_frame, text=f'{puts.iloc[i, 5]}', command=partial(cartAdd, puts, 'put', 'buy', i), bg=BG, highlightbackground=BG))
        putButtons[1][-1].place(width=50, height=20, x=400, y=20 * (y + 2))

def cartAdd(data, side, direction, idx):
    contract = Contract(data.iloc[idx, :], side, direction, idx)
    cart.append(contract)
    # cart.sort() # Figure out how to sort the cart later; Top = Buy, Call : Bottom = Put, Sell
    disp_cart()

def cartRemove(n):
    for t in zip(typeLabels, dirLabels, quantityLabels, costEntries, removeButtons):
        for i in t:
            i.destroy()

    del cart[n]

    disp_cart()

def disp_cart(): # Create buttons and labels for contracts in cart
    for t in zip(typeLabels, dirLabels, quantityLabels, costEntries, removeButtons):
        for i in t:
            i.destroy()

    costVars = []
    quantityVars = []

    for i in range(len(cart)):
        quantityVars.append(tk.IntVar())
        quantityVars[-1].set(cart[i].quantity)

        costVars.append(tk.DoubleVar())
        costVars[-1].set(cart[i].cost)

        typeLabels.append(tk.Label(left_frame, text=cart[i].side.title(), bg=HL_1, borderwidth=1, relief="solid"))
        typeLabels[-1].place(width=50, height=20, y=640 + (20 * i))

        dirLabels.append(tk.Label(left_frame, text=cart[i].direction.title(), bg=HL_1, borderwidth=1, relief="solid"))
        dirLabels[-1].place(width=50, height=20, x=50, y=640 + (20 * i))

        quantityLabels.append(tk.Entry(left_frame, textvariable=quantityVars[i], bg=HL_1, borderwidth=1, relief="solid"))
        quantityLabels[-1].place(width=50, height=20, x=100, y=640 + (20 * i))
        quantityLabels[-1].bind('<Return>', lambda event: cart[i].updateQuantity(quantityVars[i].get()))

        costEntries.append(tk.Entry(left_frame, textvariable=costVars[i], bg=HL_1, borderwidth=1, relief="solid"))
        costEntries[-1].place(width=50, height=20, x=150, y=640 + (20 * i))
        costEntries[-1].bind('<Return>', lambda event: cart[i].updateCost(costVars[i].get()))

        removeButtons.append(Button(left_frame, text='X', command=partial(cartRemove, i), bg=HL_1, highlightbackground=HL_1))
        removeButtons[-1].place(width=50, height=20, x=550, y=640 + (20 * i))

    profit()

def profit():
    # Create dataframe and range of x or price values for the profit function
    df = pd.DataFrame()
    X = np.arange(calls.iloc[0, 2] * 0.5, calls.iloc[-1, 2] * 1.2, 0.01)

    print(cart)
    for contract in cart:
        y = []
        q = contract.quantity
        k = contract.strike
        c = contract.cost 
        call = True if contract.side == 'call' else False
        buy = True if contract.direction == 'buy' else False

        # Determine if we use the call or put profit formula
        if call:
            for x in X:
                if x >= k:
                    y.append(100 * (x - k) - c * 100)
                elif x <= k:
                    y.append(-c * 100)

        elif not call:
            for x in X:
                if x <= k:
                    y.append(100 * (k -x) - c * 100)
                elif x >= k:
                    y.append(-c * 100)

        df[contract.symbol] = y
        # Adjust profit if we are writing the option
        if not buy:
            df[contract.symbol] = -df[contract.symbol] - (200 * c)

    # Sum all the contracts profit to get net profit
    df['profit'] = df.sum(axis=1)
    print(df)
    
    if len(cart) == 0:
        canvas.get_tk_widget().delete("all")
        print('Removed Canvas')
    else:
        disp_profit(X, df['profit'])

def disp_profit(X, y):
    fig = Figure(figsize=(5, 5), dpi=80)
    fig.add_subplot(111).plot(X, y)
    global canvas
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().place(right_frame, width=500, height=300, x=650, y=200)

# Create the menus
main_menu = tk.Menu(left_frame)
root.config(menu=main_menu)

# Add menu items
about_menu = tk.Menu(main_menu)
main_menu.add_cascade(label='OPC', menu=about_menu)

about_menu.add_command(label='Help', command=opc_help)
about_menu.add_command(label='Exit', command=root.quit)

# Create expiration selector
exp_list = tk.Listbox(left_frame, listvariable=oExp, bg=HL_1)
exp_list.place(width=100, height=150, x=20, y=80)
exp_list.select_set(0)

exp_list.bind('<ButtonRelease-1>', lambda event: get_data())

# Create general labels
help_label = tk.Label(left_frame, text='Enter Symbol Below', bg=HL_1)
help_label.place(width=150, height=20)

# Create entry box
symbol_entry = tk.Entry(left_frame, textvariable=symbol, bg=HL_1, justify="center")
symbol_entry.place(width=100, height=20, x=20, y=40)

symbol_entry.bind('<Return>', lambda event: get_exp())
symbol_entry.bind('<FocusOut>', lambda event: get_exp())
symbol_entry.bind('<KeyRelease>', lambda event: caps())

# Option Chain Widgets
#
#   Heading labels
strike_column = tk.Label(left_frame, text='Strike', bg=HL_1)
strike_column.place(width=50, height=20, x=300)

call_umbrella = tk.Label(left_frame, text='Calls', bg=HL_1)
call_umbrella.place(width=150, height=20, x=150)

put_umbrella = tk.Label(left_frame, text='Puts', bg=HL_1)
put_umbrella.place(width=150, height=20, x=350)

#   Call labels
call_change_column = tk.Label(left_frame, text='Change', bg=HL_1)
call_change_column.place(width=50, height=25, x=150, y=20)

call_bid_column = tk.Label(left_frame, text='Bid', bg=HL_1)
call_bid_column.place(width=50, height=25, x=200, y=20)

call_ask_column = tk.Label(left_frame, text='Ask', bg=HL_1)
call_ask_column.place(width=50, height=25, x=250, y=20)

#   Put labels
put_change_column = tk.Label(left_frame, text='Change', bg=HL_1)
put_change_column.place(width=50, height=25, x=450, y=20)

put_bid_column = tk.Label(left_frame, text='Bid', bg=HL_1)
put_bid_column.place(width=50, height=25, x=350, y=20)

put_ask_column = tk.Label(left_frame, text='Ask', bg=HL_1)
put_ask_column.place(width=50, height=25, x=400, y=20)

#   Select number of strikes shown
strike_num = ttk.OptionMenu(left_frame, numStrikes, *strikes_numList, command=set_numStrikes)
strike_num.place(width=60, height=30,  x=290, y=15)
strike_num.bind('<ButtonRelease-1>', lambda event: disp_data())
strike_num.bind('<FocusOut>', lambda even: disp_data())

root.mainloop()