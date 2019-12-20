import os
#import sys
#import time
#import json
import configparser
from pathlib import Path
from random import shuffle
from shutil import get_terminal_size

from generator.gpt2.gpt2_generator import *
from story.story_manager import *
from story.utils import *
import textwrap

#add color for windows users that install colorama
try:
    import colorama
    colorama.init()
except ModuleNotFoundError:
    pass

#perhaps all the following should be put in a seperate utils file like original
config = configparser.ConfigParser()
config.read('config.ini')
settings=config["Settings"]
colors=config["Colors"]

os.environ["TF_CPP_MIN_LOG_LEVEL"] = settings["log-level"]

if not Path('prompts', 'Anime').exists():
    import pastebin

#ECMA-48 set graphics codes for the curious. Check out "man console_codes"
def colPrint(str, col='0', wrap=True):
        if wrap and settings.getint('text-wrap-width') > 1:
            str = textwrap.fill(str, settings.getint('text-wrap-width'), replace_whitespace=False)
        print("\x1B[{}m{}\x1B[{}m".format(col, str, colors["default"]))

def colInput(str, col1=colors["default"], col2=colors["default"]):
    val=input("\x1B[{}m{}\x1B[0m\x1B[{}m".format(col1,str,col1))
    print('\x1B[0m', end='')
    return val

def getNumberInput(n):
    val=colInput("Enter a number from above (default 0):", colors["selection-prompt"], colors["selection-value"])
    if val=='':
        return 0
    elif 0>int(val) or int(val)>n:
        colPrint("Invalid choice.", colors["error"])
        return getNumberInput(n)
    else:
        return int(val)

def selectFile(p=Path('prompts')):
    if p.is_dir():
        files=[x for x in p.iterdir()]
        shuffle(files)
        for n in range(len(files)):
            colPrint('{}: {}'.format(n, re.sub(r'\.txt$', '', files[n].name)), colors["menu"])
        return selectFile(files[getNumberInput(len(files)-1)])
    else:
        with p.open() as file:
            line1=file.readline()
            rest=file.read()
        return (line1, rest)

def instructions():
    with open('interface/instructions.txt', 'r', encoding='utf-8') as file:
         colPrint(file.read(), colors["instructions"], False)


def play():
    colPrint("\nInitializing AI Dungeon! (This might take a few minutes)\n", colors["loading-message"])
    generator = GPT2Generator(
            generate_num=settings.getint('generate-num'),
            temperature=settings.getfloat("temp"),
            top_k=settings.getint("top-keks"),
            top_p=settings.getfloat("top-p"))
    story_manager = UnconstrainedStoryManager(generator)
    print("\n")

    with open("interface/mainTitle.txt", "r", encoding="utf-8") as file:
        colPrint(file.read(), colors["title"])

    with open('interface/subTitle.txt', 'r', encoding="utf-8") as file:
        cols=get_terminal_size()[0]
        for line in file:
            line=re.sub(r'\n', '', line)
            line=line[:cols]
            colPrint(re.sub(r'\|[ _]*\|', lambda x: '\x1B[7m'+x.group(0)+'\x1B[27m', line), colors["subtitle"], False)
        

    while True:
        if story_manager.story != None:
            del story_manager.story

        print("\n\n")

        colPrint("0: Pick Prompt From File (Default if you type nothing)\n1: Write Custom Prompt", colors["menu"])

        if getNumberInput(1) == 1:
            with open(Path('interface', 'prompt-instructions.txt'), 'r') as file:
                colPrint(file.read(), colors['instructions'], False)
            context=colInput('Context>', colors['main-prompt'], colors['user-text'])
            prompt=colInput('Prompt>', colors['main-prompt'], colors['user-text'])
            filename=colInput('Name to save prompt as? (Leave blank for no save): ', colors['query'], colors['user-text'])
            filename=re.sub('-$','',re.sub('^-', '', re.sub('[^a-zA-Z0-9_-]+', '-', filename)))+'.txt'
            if filename != '':
                with open(Path('prompts', filename), 'w') as f: 
                    #this saves unix style line endings which might be an issue
                    #don't know how to do this properly
                    f.write(context+'\n'+prompt+'\n')
        else:
            context, prompt = selectFile()

        instructions()

        colPrint("\nGenerating story...", colors["loading-message"])

        story_manager.start_new_story(
            prompt, context=context
        )
        print("\n")
        colPrint(str(story_manager.story), colors["ai-text"])

        while True:
            if settings.getboolean('console-bell'):
                print('\x07', end='')
            action = colInput("> ", colors["main-prompt"], colors["user-text"])
            if action == "restart":
                #rating = input("Please rate the story quality from 1-10: ")
                #rating_float = float(rating)
                #story_manager.story.rating = rating_float
                break
#            elif re.match('set', action):
#                error()
            elif action == "quit":
                #rating = input("Please rate the story quality from 1-10: ")
                #rating_float = float(rating)
                #story_manager.story.rating = rating_float
                exit()

            #elif action == "nosaving":
                #upload_story = False
                #story_manager.story.upload_story = False
                #console_print("Saving turned off.")

            elif action == "help":
                instructions()

            #elif action == "save":
            #    if upload_story:
            #        id = story_manager.story.save_to_storage()
            #        console_print("Game saved.")
            #        console_print(
            #            "To load the game, type 'load' and enter the following ID: "
            #            + id
            #        )
            #    else:
            #        console_print("Saving has been turned off. Cannot save.")

            #elif action == "load":
            #    load_ID = input("What is the ID of the saved game?")
            #    result = story_manager.story.load_from_storage(load_ID)
            #    console_print("\nLoading Game...\n")
            #    console_print(result)

            #elif len(action.split(" ")) == 2 and action.split(" ")[0] == "load":
            #    load_ID = action.split(" ")[1]
            #    result = story_manager.story.load_from_storage(load_ID)
            #    console_print("\nLoading Game...\n")
            #    console_print(result)

            elif action == "print":
                print("\nPRINTING\n")
                colPrint(str(story_manager.story), colors["print-story"])

            elif action == "revert":

                if len(story_manager.story.actions) is 0:
                    colPrint("You can't go back any farther. ", colors["error"])
                    continue

                story_manager.story.actions = story_manager.story.actions[:-1]
                story_manager.story.results = story_manager.story.results[:-1]
                colPrint("Last action reverted. ", colors["message"])
                if len(story_manager.story.results) > 0:
                    colPrint(story_manager.story.results[-1], colors["ai-text"])
                else:
                    colPrint(story_manager.story.story_start, colors["ai-text"])
                continue

            else:
                if action == "":
                    action = ""
                    result = story_manager.act(action)
                    colPrint(result, colors["ai-text"])

                elif action[0] == '"':
                    action = "You say " + action

                else:
                    action = action.strip()
                    action = action[0].lower() + action[1:]

                    if "You" not in action[:6] and "I" not in action[:6]:
                        action = "You " + action

                    if action[-1] not in [".", "?", "!"]:
                        action = action + "."

                    action = first_to_second_person(action)

                    action = "\n> " + action + "\n"

                result = "\n" + story_manager.act(action)
                if len(story_manager.story.results) >= 2:
                    similarity = get_similarity(
                        story_manager.story.results[-1], story_manager.story.results[-2]
                    )
                    if similarity > 0.9:
                        story_manager.story.actions = story_manager.story.actions[:-1]
                        story_manager.story.results = story_manager.story.results[:-1]
                        colPrint( "Woops that action caused the model to start looping. Try a different action to prevent that.", colors["error"])
                        continue

                if player_won(result):
                    colPrint(result + "\n CONGRATS YOU WIN", colors["message"])
                    break
                elif player_died(result):
                    colPrint(result, colors["ai-text"])
                    colPrint("YOU DIED. GAME OVER", colors["error"])
                    colPrint("\nOptions:\n0)Start a new game\n1)\"I'm not dead yet!\" (If you didn't actually die)", colors["menu"])
                    choice = getNumberInput(1)
                    if choice == 0:
                        break
                    else:
                        colPrint("Sorry about that...where were we?", colors["query"])
                        colPrint(result, colors["ai-text"])

                else:
                    colPrint(result, colors["ai-text"])


play()
