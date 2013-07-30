#! /usr/bin/env python

from os import path
import sys
import re
import argparse
import platform
from llvm2bpl import *

VERSION = '1.2'


def smackParser():
  parser = argparse.ArgumentParser(add_help=False, parents=[llvm2bplParser()])
  parser.add_argument('--verifier', dest='verifier', choices=['boogie-plain', 'boogie-inline', 'corral'], default='boogie-inline',
                      help='set the underlying verifier format')
  parser.add_argument('--entry-points', metavar='PROC', dest='entryPoints', default='main', nargs='+',
                      help='specify entry procedures')
  return parser


def addInline(match, entryPoints):
  procName = match.group(1)
  procDef = ''
  if procName in entryPoints:
    procDef += 'procedure ' + procName + '('
  else:
    procDef += 'procedure {:inline 1} ' + procName + '('
  return procDef


def addEntryPoint(match, entryPoints):
  procName = match.group(1)
  procDef = ''
  if procName in entryPoints:
    procDef += 'procedure {:entrypoint} ' + procName + '('
  else:
    procDef += 'procedure ' + procName + '('
  return procDef


def clang(scriptPathName, inputFile):
  scriptFullPath = path.abspath(scriptPathName)
  smackRoot = path.dirname(scriptFullPath)
  smackHeaders = path.join(smackRoot, 'include')

  fileName = path.splitext(inputFile.name)[0]

  p = subprocess.Popen(['clang', '-c', '-Wall', '-emit-llvm', '-O0', '-g',
    '-I' + smackHeaders, inputFile.name, '-o', fileName + '.bc'])
  p.wait()
  inputFileName = path.join(path.curdir, fileName + '.bc')
  inputFile = open(inputFileName, 'r')
  return inputFile


def smack(scriptPathName, inputFile, debugFlag, memmod, verifier, entryPoints):
  fileExtension = path.splitext(inputFile.name)[1]
  if fileExtension == '.c':
    # if input file is .c, then compile it first with clang
    inputFile = clang(scriptPathName, inputFile)

  debug, bpl = llvm2bpl(scriptPathName, inputFile, debugFlag, memmod)
  inputFile.close()

  # print debug info
  if debugFlag:
    print debug

  p = re.compile('procedure[ ]*([a-zA-Z0-9_]*)[ ]*\(')
  if verifier == 'boogie-inline':
    # put inline on procedures
    bpl = p.sub(lambda match: addInline(match, entryPoints), bpl)
  elif verifier == 'corral':
    # annotate entry points
    bpl = p.sub(lambda match: addEntryPoint(match, entryPoints), bpl)
  return bpl


if __name__ == '__main__':

  # parse command line arguments
  parser = argparse.ArgumentParser(description='Outputs the appropriately annotated Boogie file generated from the input LLVM file.', parents=[smackParser()])
  args = parser.parse_args()

  bpl = smack(path.dirname(sys.argv[0]), args.infile, args.debug, args.memmod, args.verifier, args.entryPoints)

  # write final output
  args.outfile.write(bpl)
  args.outfile.close()

