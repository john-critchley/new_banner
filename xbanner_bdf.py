#!/usr/bin/python

import os
import sys
import numpy as np
import pdb
import argparse
import datetime
import locale

def hex_to_bitarray(hex_str, bitorder='big'):
    if len(hex_str) % 2 != 0:
        raise ValueError("Hex string must have an even number of digits.")

    hex_bytes = [hex_str[i:i+2] for i in range(0, len(hex_str), 2)]

    uint8_arr = np.array([int(byte, 16) for byte in hex_bytes], dtype=np.uint8)

    unpacked = np.unpackbits(uint8_arr, axis=-1, bitorder=bitorder)

    return unpacked.reshape(1, -1)  # Keep as a row vector

class character:
    def __init__(self, charname, default_bounding_box):
        self.char=charname
        self.data=[]
        self.bounding_box=default_bounding_box
    def __repr__(self):
        return (
            f'{self.char=}\n'
            f'{self.enc=}\n'
            f'{self.swidth=}\n'
            f'{self.dwidth=}\n'
            f'{self.bounding_box=}\n'
            f'{self.d}'
        )
    def encoding(self, enc):
        self.enc=int(enc)
    def swidth(self, sa, sb):
        self.swidth=(sa,sb)
    def dwidth(self, da, db):
        self.dwidth=(da,db)
    def set_bounding_box(self, a,b,c,d):
        self.bounding_box=list([int(n) for n in [a,b,c,d]])
    def add_data(self, d):
        self.data.append(d)
    def done(self):
        #print(len(self.data), self.bounding_box[:2])
        box=[int(i) for i in self.bounding_box[:2]]

        #bits = np.unpackbits(np.fromiter((int(i, 16) for i in self.data), dtype=np.uint8))
        if trace:
            pdb.set_trace()
        bits = np.array([ np.unpackbits(np.uint8([ int( dd[d<<1:(d<<1)+2] , base=16 ) for d in range(len(dd)>>1)] )) for dd in self.data])

#        needed_bits = np.prod(box)  # Total bits required by the output shape

#        bits =(
#             np.pad(bits, (0, needed_bits - len(bits)))
#            if len(bits) < needed_bits else
#             bits[:needed_bits]
#            )

#        self.d=bits.reshape(*reversed(box))
        self.d=bits
        #print('>>>', self.char)
        #print(str(self))
        #print('<<<', self.char)
        #print(repr(self))
        del self.data # no longer needed as it is in d

    def __getitem__(self,pos):
        if trace:
            pdb.set_trace()
        try:
            return self.d.__getitem__(pos)
        except IndexError as ie:
            return False

    def __str__(self):
        v=np.vectorize(lambda c:'█' if c else ' ', doc="trur or false to character or blank")
        return '\n'.join((''.join(a)) for a in (v(self.d)))
    def px(self, x, y):
        return self.d[x,y]
    def print(self):
        print(self.char)
        # pdb.set_trace()
        for x in range(self.bounding_box[1]):
            for y in range(self.bounding_box[0]):
                print('█' if self[x, y] else ' ', sep='', end='')
            print()

class font:
    def __init__(self):
        self.bitmap=False
        self.chars={}
        self.default_bounding_box=None

    def __del__(self):
        pass
        # print(dir(self))

    def handle_line(self, line):
        c,*l=line.split(' ')
        a=getattr(self, c, None)
        if a is not None:
            a(*l)
        else:
            self.feed_data(line)

    def feed_data(self, data):
        if self.bitmap:
            self.curchar.add_data(data)

    def __str__(self):
        return self.fontname
    def BITMAP(self):
        self.bitmap=True
    def STARTFONT(self, fontno):
        self.characters={}
        self.fontid=fontno
    def FONT(self, *fontname):
        self.fontname=' '.join(fontname)
    def SIZE(self, a,b,c):
        pass
    def FONTBOUNDINGBOX(self, a,b,c,d):
        self.default_bounding_box=list([int(n) for n in [a,b,c,d]])
    def STARTPROPERTIES(self, sprop):
        pass
    def FONT_ASCENT(self, ascent):
        pass
    def FONT_DESCENT(self, descent):
        pass
    def DEFAULT_CHAR(self, defchar):
        pass
    def ENDPROPERTIES(self, ):
        pass
    def CHARS(self, numchars):
        self.numchars=int(numchars)
    def STARTCHAR(self, *char):
        self.curchar=character('.'.join(char), self.default_bounding_box)
    def ENCODING(self, enc):
        self.curchar.encoding(enc)
    def SWIDTH(self, sa,sb):
        self.curchar.swidth(sa, sb)
    def DWIDTH(self, da,db):
        self.curchar.dwidth(da, db)
    def BBX(self, a,b,c,d):
        self.curchar.set_bounding_box(a,b,c,d)
    def ENDCHAR(self):
        self.bitmap=False
        self.curchar.done()
        self.chars[self.curchar.enc]=self.curchar
        del self.curchar
    def ENDFONT(self):
        pass
#        print(self)
#        for c in self.chars:
#            print(c)
#            print('===')
#            c.print()
#            print('---')
#            print(repr(c))
    def fontstring(self, s):
        #return [self.chars[ord(ch)] for ch in s]
        thestring=[self.chars[ord(c)] for c in s]
        cmap=[32, 9624, 9629, 9600, 9622, 9612, 9630, 9627, 9623, 9626, 9616, 9628, 9604, 9625, 9631, 9608]
        def fn(x, y):
            x1, y1=x*2, y*2
            xc,xo=divmod(x1, self.default_bounding_box[0])
            # repeat for y when we do multi row banners
            ch=thestring[xc]
            gl=0
            for i in range(4): 
                xi=i&1 # mod 2
                yi=i>>1
                gl|=ch[y1+yi,xo+xi]<<i
            #print(gl,cmap[gl])
            return cmap[gl]
            
        return fn
        
def msg(fnt, inpstr):
        fs=(fnt.fontstring(inpstr))
        twidth,rem=divmod(fnt.default_bounding_box[0]*len(inpstr),2) # Using default bounding box assumes fixed width
        if rem:
            twidth+=1
        ll=[]
        theight,rem=divmod(fnt.default_bounding_box[1],2) # also assume 1 row
        if rem:
            theight+=1
    
        if trace:
            pdb.set_trace()
        for y in range(theight):
            l=[]
            for x in range(twidth):
                l.append(chr(fs(x, y)))
            ll.append(str().join(l))
        return '\n'.join(ll)

def main(fn, hello=["Hello"]):
    f={}
    with open(fn) as fd:
        f[fn]=font()
        for line in fd:
            line=line.rstrip()
            f[fn].handle_line(line)
    for message in hello:
        print(msg(f[fn], message))

if __name__=="__main__":
    global trace
    lc_time = os.environ.get("LC_TIME") or os.environ.get("LANG")

    if lc_time:
        try:
            locale.setlocale(locale.LC_TIME, lc_time)
        except locale.Error:
            print(f"Warning: Locale {lc_time} is not available. Using the system default.")

    parser = argparse.ArgumentParser()
    parser.add_argument("--font", '-f', help="font to read")
    parser.add_argument("--trace", "-t", action='store_true', help='enter debugger')
    parser.add_argument("--date", "-d", action='store_true', help='handle input as strftime string')
    parser.add_argument("messages", nargs='*', help='Message', default=[datetime.datetime.now().strftime("%x %T")])
    args = parser.parse_args()
    trace=args.trace
    messages=[datetime.datetime.now().strftime(m) for m in args.messages] if args.date else args.messages
    main(args.font, hello=messages)
