#!/usr/bin/python3.2

#DKA:xslamp01

import sys
import argparse
import re
import collections

#SA - stavový automat

################################################################################
# Definice tříd.

class OrderedSet(list):
	"""Třída představující množinu seřazenou podle pořadí vložení."""
	
	def __init__(self):
		super()
	
	def add(self, item):
		if item not in self:
			self.append(item)
	
	def update(self, iterable):
		if iterable is None:
			return
		else:
			for item in iterable:
				self.add(item)

class State:
	"""Třída představující jeden stav konečného automatu."""
	
	def __init__(self, name):
		"""Inicializuje objekt."""
		self.name=name
		self.transitions=set()
	
	def __repr__(self):
		"""Vrátí objekt jako řetězec."""
		return "{0}('{1}')".format(self.__class__.__name__, self.name)
	
	def __key(self):
		"""Klíč pro hashování."""
		return (self.name)
	
	def __eq__(self, x):
		return self.__key()==x.__key()
	
	def __hash__(self):
		"""Vrátí hash objektu. Potřebuje se při vytváření množin."""
		return hash(self.__key())
	
	def get_epsilons(self):
		"""Získá všechny epsilon přechody, které "vedou" skrz epsilon uzávěr přechodu."""
		
		#epsilon přechody tohoto stavu
		epsilons=OrderedSet()
		epsilons.update({item for item in self.transitions if item.char==""})
		
		#přidání epsilon přechodů stavů, do kterých se dostanu pomocí epsilon přechodů
		for item in epsilons:
			epsilons.update(item.next.get_epsilons())
		
		return epsilons
	
	def del_epsilons(self):
		"""Odstraní epsilon přechody vycházející z tohoto stavu."""

		#epsilon přechody
		epsilons=self.get_epsilons()
		
		if len(epsilons)==0:
			return
		
		#přechody, které "vedou ven" z epsilon uzávěru
		transs=set()
		for item in epsilons:
			transs.update(item.next.transitions)
		
		#odstranění epsilon přechodů
		transs={item for item in transs if item.char!=""}
		self.transitions={item for item in self.transitions if item.char!=""}
		#přidání nových přechodů, vzniklých odstraněním epsilon přechodů
		self.transitions.update({Transition(self, item.char, item.next) for item in transs})
	
	def next_states(self, char):
		"""Vrátí stavy do kterých můžeme přejít se vstupem char."""
		return {item.next for item in self.transitions if item.char==char}
	
class Transition:
	"""Třída představující přechod z jednoho stavu do druhého."""
	
	def __init__(self, state, char, next):
		"""Inicializuje objekt."""
		self.state=state
		self.char=char
		self.next=next
	
	def __repr__(self):
		"""Vrátí objekt jako řetězec."""
		if(self.char=="'"):
			return "{3}('{0}', \"{1}\", '{2}')".format(self.state.name, self.char, self.next.name, self.__class__.__name__)
		else:
			return "{3}('{0}', '{1}', '{2}')".format(self.state.name, self.char, self.next.name, self.__class__.__name__)
	
	def __key(self):
		"""Klíč pro hashování."""
		return (self.state.name, self.char, self.next.name)
	
	def __eq__(self, x):
		return self.__key()==x.__key()
	
	def __hash__(self):
		"""Vrátí hash objektu. Potřebuje se při vytváření množin."""
		return hash(self.__key())

class MultiState(State):
	"""Třída představující přechod z jednoho stavu do druhého. Každý stav je kombinace jednoho či více stavů."""
	
	def __init__(self, states):
		"""Inicializace objektu."""
		if isinstance(states, State):
			self.states=set()
			self.states.add(states)
			self.name=states.name
			self.transitions=set()
		else:
			self.states=states
			self.name="_".join(sorted([state.name for state in states]))
			self.transitions=set()

################################################################################
# Definice funkcí.

def code(char):
	if char=="'":
		return "''"
	else:
		return char

def print_SM():
	"""Vytiskne stavový automat po odstranění epsilon přechodů."""
	
	print("(\n{"+", ".join(sorted([item for item in states.keys()]))+"},\n"+"{"+", ".join(sorted({"'"+code(item)+"'" for item in chars}))+"},\n"+"{"+",".join(sorted(["\n"+item.state.name+" "+"'"+code(item.char)+"'"+" -> "+item.next.name for item in transitions]))+"\n},\n"+start.name+",\n"+"{"+", ".join(sorted([item.name for item in final]))+"}\n"+")", end="", file=output_file)

def print_MSM():
	"""Vytiskne stavový automat po odstranění nedeterminizmu."""
	
	print("(\n{"+", ".join(sorted([item for item in multi_states.keys()]))+"},\n"+"{"+", ".join(sorted({"'"+code(item)+"'" for item in chars}))+"},\n"+"{"+",".join(sorted(["\n"+item.state.name+" "+"'"+code(item.char)+"'"+" -> "+item.next.name for item in multi_transitions]))+"\n},\n"+start.name+",\n"+"{"+", ".join(sorted([item.name for item in multi_final]))+"}\n"+")", end="", file=output_file)

def end(exit_code):
	"""Ukončí program s návratovým kódem exit_code."""
	if options.input:
		input_file.close()

	if options.output:
		output_file.close()
	
	exit(exit_code)

################################################################################
# Začátek skriptu.

#analýza přepínačů na příkazové řádce
parser=argparse.ArgumentParser(description='2nd IPP project: DKA')

parser.add_argument('--input', action="store", default=False, help="vstupní soubor")
parser.add_argument('--output', action="store", default=False, help="výstupní soubor")
parser.add_argument('-e', '--no-epsilon-rules', action="store_true", default=False, help="odstranění epsilon pravidel")
parser.add_argument('-d', '--determinization', action="store_true", default=False, help="determinizace konečného automatu")
parser.add_argument('-i', '--case-insensitive', action="store_true", default=False, help="nebere ohled na velikost písmen")

options=parser.parse_args(sys.argv[1:])

if options.input:
	input_file=open(options.input, "r")
else:
	input_file=sys.stdin

if options.output:
	output_file=open(options.output, "w")
else:
	output_file=sys.stdout

#kontrola přepínačů
if options.no_epsilon_rules and options.determinization:
	print("Nastala chyba: Nepovolená kombinace přepínačů.", file=sys.stderr)
	end(1)

#
#Kontrola vstupního souboru.
#

#nahrání vstupního souboru do řetězce a odstranění komentářů
string=''.join(input_file).strip()

if options.case_insensitive:
	string=string.lower()

string=re.sub(r"(?<!')#(?!')[^\n]*\n", "", string)
string=re.sub(r"(?<!')#(?!')[^\n]*$", "", string)

#kontrola uvozovek
if re.search(r"[^'][^']+'[^'][^']+", string, re.DOTALL):
	print("Nastala chyba: Mezi uvozovkami je více znaků.", file=sys.stderr)
	end(40)

#všecny skupiny bílých znaků jsou nahrazeny mezerou
string=re.sub("(?<!')\s+(?!')", " ", string)

#odstranění přebytečných mezer
string=re.sub(r"(?<![A-Za-z0-9_'])\s(?!')", "", string)
string=re.sub(r"(?<=[A-Za-z0-9_'])\s(?=[-,}{])", "", string)
string=re.sub(r"(?<=')\s(?!')", "", string)
string=re.sub(r"(?<!')\s(?=')", "", string)

#vytvoření regulární výrazu popisující SA
first=  r"\{([A-Za-z_][A-Za-z0-9_]*,){,}([A-Za-z_][A-Za-z0-9_]*){1}\},"
second= r"(\{((([^\(\)\{\}\->,.|#\s])|('.')|('''')),){,}(([^\(\)\{\}\->,.|#\s])|('.')|('''')){1}\})|(\{\}),"
third1= r"\{((([A-Za-z_][A-Za-z0-9_]*'((.?)|(''))'\->[A-Za-z_][A-Za-z0-9_]*)|(([A-Za-z_][A-Za-z0-9_]* [^\(\)\{\}\->,.|#\s]\->[A-Za-z_][A-Za-z0-9_]*))|(([A-Za-z_][A-Za-z0-9_]*\->[A-Za-z_][A-Za-z0-9_]*))),){,}"
third2=    r"(([A-Za-z_][A-Za-z0-9_]*'((.?)|(''))'\->[A-Za-z_][A-Za-z0-9_]*)|(([A-Za-z_][A-Za-z0-9_]* [^\(\)\{\}\->,.|#\s]\->[A-Za-z_][A-Za-z0-9_]*))|(([A-Za-z_][A-Za-z0-9_]*\->[A-Za-z_][A-Za-z0-9_]*))){1}\},"
fourth= r"[A-Za-z_][A-Za-z0-9_]*,"
fifth=  r"\{([A-Za-z_][A-Za-z0-9_]*,){,}([A-Za-z_][A-Za-z0-9_]*){1}\}"

if not re.match(r"\A\("+first+second+third1+third2+fourth+fifth+r"\)\Z", string, re.DOTALL):
	print("Nastala chyba: vstup není stavový automat.", file=sys.stderr)
	end(40)

string=string[1:-1]

#vytvoření množiny stavů (instancí třídy State)
index=string.index("},{")
states_string=string[1:index]
string=string[index+2:]

state_names=set(states_string.split(","))

for name in state_names:
	if name[0]=='_' or name[-1]=='_':
		print("Nastala chyba: stav začíná nebo končí podtržítkem.", file=sys.stderr)
		end(40)	

states=dict()
states={name: State(name) for name in state_names}

if not states:
	print("Nastala chyba: Množina stavů je prázdná.", file=sys.stderr)
	end(40)

#vytvoření vstupní abecedy
index=string.index("},{")
chars_string=string[1:index]
string=string[index+2:]

if not chars_string:
	print("Nastala chyba: Vstupní abeceda je prázdná.", file=sys.stderr)
	end(41)

chars=set()
chars={name for name in chars_string.split(",")}

new_chars=set()
for item in chars:
	if item=="'''":
		print("Nastala chyba: množina vstupů obsahuje '''.", file=sys.stderr)
		end(40)
	elif re.match("'.'", item):
		new_chars.add(item[1])
	elif item=="''''":
		new_chars.add("'")
	elif item=="'":
		new_chars.add(",")
	else:
		new_chars.add(item)

chars=new_chars

#vytvoření množiny přechodů (instancí třídy Transition)
index=string.index("},")
transitions_string=string[1:index]
string=string[index+2:]

transitions=set()
if transitions_string!="":
	for item in re.split("(?<!'),(?!')", transitions_string):
		tmp=re.match("^([A-Za-z_][A-Za-z0-9_]*)(.*)\->([A-Za-z_][A-Za-z0-9_]*)$", item)
		state=tmp.group(1)
		char=tmp.group(2)
		next=tmp.group(3)
	
		char_len=len(char)
	
		if char_len==0 or char=="''":
			char=""
		elif char_len==2 or char_len==3:
			char=char[1]
		else:
			char="'"
	
		if state not in state_names or next not in state_names:
			print("Nastala chyba: Stav uvedený v množině přechodů není součástí množiny stavů.", file=sys.stderr)
			end(41)
		if char!="" and char not in chars:
			print("Nastala chyba: Vstup uvedený v množině přechodů není součástí množiny vstupů.", file=sys.stderr)
			end(41)
	
		transitions.add(Transition(states[state], char, states[next]))

#identifikace počátečního stavu
index=string.index(",{")
start_name=string[0:index]
string=string[index+2:]

if start_name not in state_names:
	print("Nastala chyba: Počáteční stav není součástí množiny stavů.", file=sys.stderr)
	end(41)
else:
	start=states[start_name]

#vytvoření množiny koncových stavů (instancí třídy State)
index=string.index("}")
final_string=string[0:index]
string=string[index+1:]

final=set()
if final_string!="":
	final={State(s) for s in final_string.split(",")}	
	for name in final:
		if name not in states.values():
			print("Nastala chyba: Koncový stav není součástí množiny stavů.", file=sys.stderr)
			end(41)

if string!="":
	print("Nastala chyba: Za definicí automatu jsou znaky.", file=sys.stderr)
	end(40)

#"spojení" stavů pomocí přechodů
for item in transitions:
	states[item.state.name].transitions.add(item)

#odstranění epsilon přechodů
if options.no_epsilon_rules or options.determinization:
	for item in states.values():
		item.del_epsilons()
	
	transitions=set()
	for item in states.values():
		transitions.update(item.transitions)

#pokud se mají jenom odstranit epsilon přechody
if options.no_epsilon_rules and not options.determinization:
	print_SM()
	end(0)

#odstranění nedeterminizmu
if options.determinization:
	multi_states=collections.OrderedDict()
	multi_start=MultiState(start)
	multi_states[start.name]=multi_start
	
	multi_final=set()
	
	#vytvoření množiny stavů
	for mstate in multi_states.values():
		#pro každý možný vstup s vytvoří samostaný stav
		for char in chars:
			tran=set()
			#stavy, do kterých se můžeme dostat ze současného se vstupem char
			for state in mstate.states:
				tran.update(state.next_states(char))
			#jméno nového stavu
			name="_".join(sorted([state.name for state in tran]))
			if name=="":
				continue
			#pokud stav nový stav neexistuje vytvoří se
			if name not in multi_states:
				multi_states[name]=MultiState(tran)
			multi_states[mstate.name].transitions.add(Transition(mstate, char, multi_states[name]))
		
		#vložení do množiny koncových stavů, pokud je stav koncový
		for state in mstate.states:
			if state in final:
				multi_final.add(mstate)
				break
	
	#vytvoření nové množiny přechodů
	multi_transitions=set()
	for mstate in multi_states.values():
		multi_transitions.update(mstate.transitions)
	
	print_MSM()
	end(0)
else:
	print_SM()
	end(0)

