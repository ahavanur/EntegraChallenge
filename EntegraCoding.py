print ("Initializing...")

from nltk import tokenize, pos_tag
import re
import os

class invalidInputError():
	"""Raised when OCR output not up to specification"""
	pass

class ContactInfo: 
	def __init__(self, Name, Number, eMail): 
		self.Name = Name
		self.Number = Number
		self.eMail = eMail 

class BusinessCardParser:

	# Break text into lines 
	# Assume card is split by lines using tab or newline
	def byLine(self, card):
		if card.find("\n") >= 0: 
			return card.split("\n")
		elif card.find("\t") >= 0: 
			return card.split("\t")
		else: 
			raise invalidInputError

	# Find line with highest probability of being or having a name
	# Cases to look out for: 
	# 	- Confusing company name or job title as the name
	# 	- Name not being only string in line
	# 	- Titles or suffixes 
	# 	- Middle Name
	# Assumptions: 
	# 	- All names start wtih a capital letter, have length > 1
	# 	- First names may not have anything other than 1 uppercase 
	#	  and rest lowercase letters
	def getName(self, lines):
		nameRegEx = re.compile(r"^[A-Z]([a-z]+)\s([A-Za-z']+)")
		indicator = re.compile(r'[N|n]ame:')
		poss = []
		for line in lines: 
			if len(line.split(" ")) > 2: 
				continue
			# If card has indicators ("Name: ..."); extract only Name
			if re.search(indicator,line):
				return line[indicator.search(line).span()[1]:].lstrip()
			if re.search(nameRegEx, line):
				poss.append(line)
		if len(poss) == 0: 
			return "None"
		elif len(poss) == 1: 
			return nameRegEx.search(poss[0]).group()
		else: 
			# CASE: Multiple lines that could qualify as a name
			# SOLN: NLP analysis, assign scores to each possibility
			# Choose sentence (line) with highest score; if multiple, choose latest
			maxScore = -2
			maxLines = []
			for sent in poss: 
				score = 0
				# Tag part of speech
				UCtags = pos_tag(tokenize.word_tokenize(sent))
				for wordtag in UCtags: 
					# For each tag, if it is not NNP (proper noun), deduct score
					tag = wordtag[1]
					if tag != 'NNP': 
						score -= 1
				# Normalize scores
				normScore = 1.0 + (float(score) / float(len(UCtags)))
				if normScore > maxScore: 
					maxScore = normScore
					maxLines = [sent]
				elif maxScore == normScore:
					maxLines.append(sent)
			if len(maxLines) == 1: 
				return maxLines[0]
			else: 
				# If we still have multiple possibilities, transform to lowercase and use same apprach
				# This weeds out titles like 'software engineer', which are more easily recognizable 
				# by NLTK as non-proper nouns in lowercase form
				# This process may seem redundant, but is kept separate from the first pos_tagging 
				# for optimization measures 
				maxScore = -2
				finalMaxLine = None
				for sent in maxLines: 
					score = 0
					# Tag part of speech
					LCtags = pos_tag(tokenize.word_tokenize(sent.lower()))
					for wordtag in LCtags: 
						# For each tag, if it is not NNP (proper noun), deduct score
						tag = wordtag[1]
						if tag != 'NNP': 
							score -= 1
					# Normalize scores
					normScore = 1.0 + (float(score) / float(len(UCtags)))
					# If there are still equally possible 'names' at this point, choose the first one
					if normScore > maxScore: 
						maxScore = normScore
						finalMaxLine = sent
				return finalMaxLine

	# Matches a phone number format 
	# In case of multiple (fax), take the first (usually will be desired)
	# Deal with extensions?
	def getPhoneNumber(self, lines):
		numRegEx = re.compile(r'(\+\d+|)(.|)\d\d\d(.|)(.|)\d\d\d(.|)\d\d\d\d')
		indicator = re.compile(r'[Tel|Phone|Phone Number|#]:')
		# Loop through all lines in order

		for line in lines: 
			# Remove whitsepace from line
			line.replace(" ", "")
			if numRegEx.search(line):
				digits = [str(x) for x in line if x.isdigit()]
				number = "".join(digits)
				if len(number) >= 10 and len(number) < 12: 
					return number
			if re.search(indicator,line):
				digits = [str(x) for x in line if x.isdigit()]
				number = "".join(digits)
				if len(number) >= 10 and len(number) < 12: 
					return number
		return ""

	def getEmailAddress(self, lines):
		emRegEx = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
		# Loop through all lines in order
		for line in lines: 
			# Remove whitsepace from line
			if emRegEx.search(line):
				return emRegEx.search(line).group()
		return ""


	def getContactInfo(self, card):
		lines = self.byLine(card)
		return ContactInfo(self.getName(lines), self.getPhoneNumber(lines), self.getEmailAddress(lines))

x = BusinessCardParser()

cards = os.listdir("business_cards")
for card in cards: 
	info = (x.getContactInfo(card = open("business_cards/" + card, "r").read()))

	print("Name: " + str(info.Name))
	print("Number: " + info.Number)
	print("EMail: " + info.eMail)