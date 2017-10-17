# RPGDice Bot - A Telegram bot to roll dice for RPG games
# Copyright (C) 2017  jolmopar jose@bytx.ie

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""This module contains the base object that setups the RPG Dice Bot."""

import random
import logging
import re

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import RegexHandler

class RPGDicebot(object):
    """ RPGDicebot implements the Handler methods logic for the Die rolling bot """

    def __init__(self):
        """ Initialiaze the bot operations:
            - Logging
            - Event Handler
            - Dispatcher
            - Command Handlers
        """
        # Initialize logging
        logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Create the EventHandler and pass it the bot's token.
        self.updater = Updater("your telegram token here")

        # Get the dispatcher to register handlers
        self.dp = self.updater.dispatcher

        # Command Handlers
        self.dp.add_handler(CommandHandler('game', self.setupgame, pass_chat_data=True))
        self.dp.add_handler(CommandHandler('epicquote', self.epic_quote))
        self.dp.add_handler(CommandHandler('coin', self.toss_coin))
        self.dp.add_handler(CommandHandler('ini', self.initiative))
        self.dp.add_handler(RegexHandler(r'^/\d*[dD]\d+(?:[+\-]?[\d]+)*(?:@Rolemartes2Bot)?$',
                                         self.roll_dice, pass_chat_data=True))

        # log all errors
        self.dp.add_error_handler(self.log_error)

    def log_error(self, bot, update, error):
        self.logger.warn('Update "%s" caused error "%s"' % (update, error))

    def setupgame(self, bot, update, chat_data):
        """ Setup play session parameters.
            Use this handler to store what type of game we are playing.
            The chat_data collection can be passed to other
            message handlers that may use game session parameters to
            behave differently. """

        message = update.message.text[6:]   # Strip out the '/start' Command

        # D&D
        if message.upper() == 'D&D':
            chat_data['game'] = 'D&D'
            reply = ("D&D game setup. Special features:\n"
                     "  /ini player1,player2,player3+2,... -> roll for initiative\n"
                     "  /1d20 -> 20 - Critical, 1 - Failure")
        # Add other game options here
        # elif message.upper() == 'xxxxxx':
        #    chat_data['game'] = 'xxxxxx'
        #    reply = ("xxxxxx game setup. Special features:\n"
        #             "  blah, blah...")"""

        # If an unknown game, clear game session parameters and repy with some clues
        else:
            if 'game' in chat_data:
                del chat_data['game']

            reply = ("I don't know that game, Profesor Falken.\n"
                     "Fancy a game of chess?\n"
                     "Or try D&D.")

        update.message.reply_text(reply, quote=False)

    def epic_quote(self, bot, update):
        """ Just some fun quotes to liven up the mood ;) """
        quotes = (
                "If plan A didn’t work, the alphabet has 25 more letters!",
                "Make my day, punk!",
                "I find your lack of faith disturbing.",
                "Are you talking to me?",
                "We are going to need a bigger boat...",
                "Here's Jooooohnny!",
                "So many assholes, so little bullets.",
                "It's a trap!!!",
                "One does not just walk into Mordor...",
                "Ph'nglui mglw'nafh Cthulhu R'lyeh wgah'nagl fhtagn.",
        )
        
        update.message.reply_text(random.choice(quotes), quote=False)

    def toss_coin(self, bot, update):
        """ Toss a coin """
        toss = random.randint(1, 2)
        # Format the reply
        reply = update.message.from_user.first_name
        reply += ' - \u2B55' if toss == 1 else ' - \u274C'
        update.message.reply_text(reply, quote=False)

    def _failure(self):
        """ Add some messages to make fun of the poor loosers """
        msg = (
            "Ouch!!!",
            "I find your lack of luck disturbing.",
        )

        return random.choice(msg)

    def _critical(self):
        """ Add some epic message to celebrate """
        msg = (
            "Take that!!!",
            "Yipi-kay-yey motherfuckers!",
        )

        return random.choice(msg)

    def _get_modifier(self, mod_str):
        pos = re.search(r'[\+-]\d+', mod_str)
        return(0 if not pos else int(pos.group(0)))

    def _d_and_d_extras(self, times, sides, roll):
        """ Special features when playing a D&D session """
        # Check for natural 1 and 20
        extra = ''
        if times == 1 and sides == 20:
            if roll[0] == 20:
                extra = '\n' + self._critical()
            elif roll[0] == 1:
                extra = '\n' + self._failure()
        
        return(extra)

    def _roll(self, times, sides):
        # Roll dice
        roll = [0] * times
        for i in range(times):
            roll[i] = random.randint(1, sides)

        return(roll)
        
    def roll_dice(self, bot, update, chat_data):
        """ Decode what type of dice and how many to roll.
            The chat_data collection is passed here so we
            can add special features for some game types. """
        message = update.message.text
        if bot.username in message:
            message = message[0:message.find('@')]
        message = message.lower()

        params = re.split(r'[\+-]', message[1:])
        mod = self._get_modifier(message)

        dice = params[0].split('d')
        if dice[0] == '':
            times = 1
        else:
            times = int(dice[0])

        sides = int(dice[1])

        roll = self._roll(times, sides)
                    
        sm = sum(roll) + mod

        # Format the reply
        reply = '{to} - {d}'.format(to=update.message.from_user.first_name, d=roll)
        if len(roll) > 1 or mod != 0:
            if mod != 0:
                reply += ' {b:+}'.format(b=mod)
            reply += ' = {s}'.format(s=sm)

        # Add special features if we know the game session type
        if 'game' in chat_data and chat_data['game'] == 'D&D':
            reply += self._d_and_d_extras(times, sides, roll)
                
        update.message.reply_text(reply, quote=False)

    def initiative(self, bot, update):
        """ D&D game, rolls for initiative.
            Extracts the names of the people in the fight and rolls,
            then adds any modifier and replies with the initiative order.
            Example command: /ini player1, player2+2, player2, orc1, orc2+1"""
        message = update.message.text[4:]   # Strip out the '/ini' Command
        ini = {}

        for n in message.split(','):
            name = (re.split(r'[\+-]', n)[0]).strip()
            roll = self._roll(1, 20)[0]
            roll += self._get_modifier(n)

            if roll in ini:
                ini[roll] += '/{n}'.format(n=name)
            else:
                ini[roll] = name

        # Sort the reply by higher initiative roll
        reply = ''
        for k in sorted(ini.keys(), reverse=True):
            reply += '{n} ({r}), '.format(n=ini[k], r=k)
        
        update.message.reply_text(reply[:-2], quote=False)

    def start(self):
        """ Start the bot """
        self.updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()


def main():
    """ Get the handler bot """
    bot = RPGDicebot()
    bot.start()


if __name__ == '__main__':
    main()
