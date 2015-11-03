#!/usr/bin/env python


# Copyright 2015 Ryan Wick

# This file is part of Catpac.

# Catpac is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free 
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.

# Catpac is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.

# You should have received a copy of the GNU General Public License along with
# Catpac.  If not, see <http:# www.gnu.org/licenses/>.



from __future__ import division
from __future__ import print_function
import sys
import subprocess
import os
import argparse
import shutil
import random



def main():

    args = getArguments()

    # Run the tests
    for i in range(args.number):
        print("\nTest " + str(i+1) + ":")
        if fiftyPercentChance():
            runSingleCatpacSnpTest()
        else:
            runSingleCatpacDeletionTest()


def getArguments():
    
    parser = argparse.ArgumentParser(description='Catpac tester', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-n', '--number', type=int, action='store', help='The number of random tests to conduct', default=50)

    return parser.parse_args()



def runSingleCatpacSnpTest():

    # Make a temporary directory for the alignment files.
    testdir = os.getcwd() + '/test'
    if not os.path.exists(testdir):
        os.makedirs(testdir)

    # Create two random sequences which share a region in common.
    seq1UniqueLength1 = random.randint(0, 200)
    seq2UniqueLength1 = random.randint(0, 200)
    sharedLength = random.randint(100, 1000)
    seq1UniqueLength2 = random.randint(0, 200)
    seq2UniqueLength2 = random.randint(0, 200)
    sharedSequence = getRandomDNASequence(sharedLength)
    sequence1 = getRandomDNASequence(seq1UniqueLength1) + sharedSequence + getRandomDNASequence(seq1UniqueLength2)
    sequence2 = getRandomDNASequence(seq2UniqueLength1) + sharedSequence + getRandomDNASequence(seq2UniqueLength2)

    # Create 5 random SNPs in the shared region of sequence 2
    startOfSnpRegion = seq2UniqueLength1 + 10
    endOfSnpRegion = seq2UniqueLength1 + sharedLength - 10
    snpLocationsSeq2 = getUniqueRandomNumbers(startOfSnpRegion, endOfSnpRegion, 5)
    for snpLocationSeq2 in snpLocationsSeq2:
        sequence2 = createSnp(sequence2, snpLocationSeq2)
    additionalBasesAtStartOfSeq1 = seq1UniqueLength1 - seq2UniqueLength1
    snpLocationsSeq1 = []
    for snpLocationSeq2 in snpLocationsSeq2:
        snpLocationsSeq1.append(snpLocationSeq2 + additionalBasesAtStartOfSeq1)

    # Half the time, flip sequence 1 to its reverse complement.
    if fiftyPercentChance():
        sequence1 = getReverseComplement(sequence1)

    # Save the sequences to FASTA files
    sequence1FilePath = testdir + "/seq1.fasta"
    sequence2FilePath = testdir + "/seq2.fasta"
    saveSequenceToFile("NODE_1_length_" + str(len(sequence1)) + "_cov_100.0", sequence1, sequence1FilePath)
    saveSequenceToFile("NODE_2_length_" + str(len(sequence2)) + "_cov_100.0", sequence2, sequence2FilePath)

    # Run Catpac on the two sequences and save the variants to file.
    variantsFilePath = testdir + "/variants.csv"
    catpacCommand = ["./catpac.py", sequence1FilePath, sequence2FilePath, "-l", "50", "-i", "90", "-v", variantsFilePath]
    p = subprocess.Popen(catpacCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    # We expect to find the SNPs where we put them (plus 1 due to 0 vs 1 based
    # indexing).
    expectedSnpLocations = []
    for i in range(len(snpLocationsSeq1)):
        snpLocation1 = snpLocationsSeq1[i] + 1
        snpLocation2 = snpLocationsSeq2[i] + 1
        expectedSnpLocations.append((snpLocation1, snpLocation2))
    expectedSnpLocations.sort()

    # Look in the variants file for where the SNPs were actually found.
    actualSnpLocations = []
    variantsFile = open(variantsFilePath, 'r')
    for line in variantsFile:
        if line[0:3] == "SNP":
            lineParts = line.split(",")
            actualSnpLocations.append((int(lineParts[4]), int(lineParts[9])))

    # Exclude SNPs that aren't in the shared region.
    filteredActualSnpLocations = []
    for actualSnpLocation in actualSnpLocations:
        seq1Location = actualSnpLocation[0]
        seq2Location = actualSnpLocation[1]
        if seq1Location > seq1UniqueLength1 and seq1Location < seq1UniqueLength1 + sharedLength and seq2Location > seq2UniqueLength1 and seq2Location < seq2UniqueLength1 + sharedLength:
            filteredActualSnpLocations.append(actualSnpLocation)
    actualSnpLocations = filteredActualSnpLocations
    actualSnpLocations.sort()

    # Make sure each of the expected SNPs is in the actual SNPs.
    testPassed = True
    for expectedSnpLocation in expectedSnpLocations:
        if expectedSnpLocation not in actualSnpLocations:
            testPassed = False
            break

    # Make sure the number of found SNPs is the number of expected SNPs:
    if len(actualSnpLocations) != len(expectedSnpLocations):
        testPassed = False

    print("Expected SNP locations:", expectedSnpLocations)
    print("Actual SNP locations:  ", actualSnpLocations)

    if testPassed:
        print("PASS")
    else:
        print("FAIL")
        quit()

    # Delete the temporary files.
    if os.path.exists(testdir):
        shutil.rmtree(testdir)




def runSingleCatpacDeletionTest():

    # Make a temporary directory for the alignment files.
    testdir = os.getcwd() + '/test'
    if not os.path.exists(testdir):
        os.makedirs(testdir)

    # Create two random sequences which share a region in common.
    seq1UniqueLength1 = random.randint(0, 200)
    seq2UniqueLength1 = random.randint(0, 200)
    sharedLength = random.randint(200, 1000)
    seq1UniqueLength2 = random.randint(0, 200)
    seq2UniqueLength2 = random.randint(0, 200)
    sharedSequence = getRandomDNASequence(sharedLength)
    sequence1 = getRandomDNASequence(seq1UniqueLength1) + sharedSequence + getRandomDNASequence(seq1UniqueLength2)
    sequence2 = getRandomDNASequence(seq2UniqueLength1) + sharedSequence + getRandomDNASequence(seq2UniqueLength2)

    # Create 5 random deletions in the shared region of sequence 2
    startOfDeletionRegion = seq2UniqueLength1 + 10
    endOfDeletionRegion = seq2UniqueLength1 + sharedLength - 10
    deletionLocationsSeq2 = getRandomDeletionLocations(startOfDeletionRegion, endOfDeletionRegion, 5, 10, sequence2)
    deletionLocationsSeq2.sort(reverse=True)

    for deletionLocationSeq2 in deletionLocationsSeq2:
        sequence2 = createDeletion(sequence2, deletionLocationSeq2)
    additionalBasesAtStartOfSeq1 = seq1UniqueLength1 - seq2UniqueLength1
    deletionLocationsSeq1 = []
    for deletionLocationSeq2 in deletionLocationsSeq2:
        deletionLocationsSeq1.append(deletionLocationSeq2 + additionalBasesAtStartOfSeq1)
    deletionLocationsSeq1.sort()
    deletionLocationsSeq2.sort()
    for i in range(5):
        deletionLocationsSeq2[i] = deletionLocationsSeq2[i] - i

    # Half the time, flip sequence 1 to its reverse complement.
    if fiftyPercentChance():
        sequence1 = getReverseComplement(sequence1)

    # Save the sequences to FASTA files
    sequence1FilePath = testdir + "/seq1.fasta"
    sequence2FilePath = testdir + "/seq2.fasta"
    saveSequenceToFile("NODE_1_length_" + str(len(sequence1)) + "_cov_100.0", sequence1, sequence1FilePath)
    saveSequenceToFile("NODE_2_length_" + str(len(sequence2)) + "_cov_100.0", sequence2, sequence2FilePath)

    # Run Catpac on the two sequences and save the variants to file.
    variantsFilePath = testdir + "/variants.csv"
    catpacCommand = ["./catpac.py", sequence1FilePath, sequence2FilePath, "-l", "50", "-i", "90", "-v", variantsFilePath]
    p = subprocess.Popen(catpacCommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()

    # We expect to find the deletions where we put them (plus 1 due to 0 vs 1
    # based indexing).
    expectedDeletionLocations = []
    for i in range(len(deletionLocationsSeq1)):
        deletionLocation1 = deletionLocationsSeq1[i] + 1
        deletionLocation2 = deletionLocationsSeq2[i] + 1
        expectedDeletionLocations.append((deletionLocation1, deletionLocation2))
    expectedDeletionLocations.sort()

    # Look in the variants file for where the indels were actually found.
    actualDeletionLocations = []
    variantsFile = open(variantsFilePath, 'r')
    for line in variantsFile:
        if line[0:5] == "indel":
            lineParts = line.split(",")
            actualDeletionLocations.append((int(lineParts[4]), int(lineParts[9])))

    # Exclude indels that aren't in the shared region.
    filteredActualDeletionLocations = []
    for actualDeletionLocation in actualDeletionLocations:
        seq1Location = actualDeletionLocation[0]
        seq2Location = actualDeletionLocation[1]
        if seq1Location > seq1UniqueLength1 and seq1Location < seq1UniqueLength1 + sharedLength and seq2Location > seq2UniqueLength1 and seq2Location < seq2UniqueLength1 + sharedLength - 5:
            filteredActualDeletionLocations.append(actualDeletionLocation)
    actualDeletionLocations = filteredActualDeletionLocations
    actualDeletionLocations.sort()

    # Make sure each of the expected deletions is in the actual deletions.
    testPassed = True
    for expectedDeletionLocation in expectedDeletionLocations:
        if expectedDeletionLocation not in actualDeletionLocations:
            testPassed = False
            break

    print("Expected deletion locations:", expectedDeletionLocations)
    print("Actual deletion locations:  ", actualDeletionLocations)

    if testPassed:
        print("PASS")
    else:
        print("FAIL")
        quit()

    # Delete the temporary files.
    if os.path.exists(testdir):
        shutil.rmtree(testdir)





def getRandomDNASequence(length):
    randomSequence = ""
    for i in range(length):
        randomSequence += getRandomBase()
    return randomSequence


def getRandomBase():
    randomNum = random.randint(1, 4)
    if randomNum == 1:
        return "A"
    elif randomNum == 2:
        return "C"
    elif randomNum == 3:
        return "G"
    else:
        return "T"


def getUniqueRandomNumbers(rangeStart, rangeEnd, count):
    randomNumbers = []
    for i in range(count):
        randomNumber = random.randint(rangeStart, rangeEnd)
        while randomNumber in randomNumbers:
            randomNumber = random.randint(rangeStart, rangeEnd)
        randomNumbers.append(randomNumber)
    return randomNumbers



# This function finds random locations for making deletions.  It has a couple
# of criteria for these locations:
#   - there can't be any nearby identical bases
#   - they must be sufficiently spaced
def getRandomDeletionLocations(rangeStart, rangeEnd, count, spacing, sequence):
    randomNumbers = []
    for i in range(count):
        randomNumber = random.randint(rangeStart, rangeEnd)
        while numberCloseToNumbersInList(randomNumber, randomNumbers, spacing) or \
              sequence[randomNumber] == sequence[randomNumber-1] or \
              sequence[randomNumber] == sequence[randomNumber+1] or \
              sequence[randomNumber] == sequence[randomNumber-2] or \
              sequence[randomNumber] == sequence[randomNumber+2]:
            randomNumber = random.randint(rangeStart, rangeEnd)
        randomNumbers.append(randomNumber)
    return randomNumbers



def numberCloseToNumbersInList(number, numberList, distance):
    for eachNumber in numberList:
        if abs(number - eachNumber) < distance:
            return True
    return False



def createSnp(sequence, location):
    oldBase = sequence[location]
    newBase = getRandomBase()
    while newBase == oldBase:
        newBase = getRandomBase()
    return sequence[0:location] + newBase + sequence[location+1:]



def createDeletion(sequence, location):
    return sequence[0:location] + sequence[location+1:]



def saveSequenceToFile(sequenceName, sequence, filename):
    outfile = open(filename, 'w')
    outfile.write('>' + sequenceName + '\n')
    while len(sequence) > 60:
        outfile.write(sequence[0:60] + '\n')
        sequence = sequence[60:]
    outfile.write(sequence + '\n')



def getReverseComplement(forwardSequence):

    reverseComplement = ""
    for i in reversed(range(len(forwardSequence))):
        base = forwardSequence[i]

        if base == 'A': reverseComplement += 'T'
        elif base == 'T': reverseComplement += 'A'
        elif base == 'G': reverseComplement += 'C'
        elif base == 'C': reverseComplement += 'G'
        elif base == 'a': reverseComplement += 't'
        elif base == 't': reverseComplement += 'a'
        elif base == 'g': reverseComplement += 'c'
        elif base == 'c': reverseComplement += 'g'
        elif base == 'R': reverseComplement += 'Y'
        elif base == 'Y': reverseComplement += 'R'
        elif base == 'S': reverseComplement += 'S'
        elif base == 'W': reverseComplement += 'W'
        elif base == 'K': reverseComplement += 'M'
        elif base == 'M': reverseComplement += 'K'
        elif base == 'r': reverseComplement += 'y'
        elif base == 'y': reverseComplement += 'r'
        elif base == 's': reverseComplement += 's'
        elif base == 'w': reverseComplement += 'w'
        elif base == 'k': reverseComplement += 'm'
        elif base == 'm': reverseComplement += 'k'
        elif base == 'B': reverseComplement += 'V'
        elif base == 'D': reverseComplement += 'H'
        elif base == 'H': reverseComplement += 'D'
        elif base == 'V': reverseComplement += 'B'
        elif base == 'b': reverseComplement += 'v'
        elif base == 'd': reverseComplement += 'h'
        elif base == 'h': reverseComplement += 'd'
        elif base == 'v': reverseComplement += 'b'
        elif base == 'N': reverseComplement += 'N'
        elif base == 'n': reverseComplement += 'n'
        elif base == '.': reverseComplement += '.'
        elif base == '-': reverseComplement += '-'
        elif base == '?': reverseComplement += '?'
        else: reverseComplement += 'N'

    return reverseComplement


def fiftyPercentChance():
    return random.randint(0, 1) == 0


# Standard boilerplate to call the main() function to begin the program.
if __name__ == '__main__':
    main()