import sys
import time
import re

def format_value_name (setting_name, value_name):

    if (setting_name[-3:] == "DIV" and value_name[:4] == "DIV_"):
        value_name = value_name[4:]
    elif (setting_name[-3:] == "MUL" and value_name[:4] == "MUL_"):
        value_name = value_name[4:]
    elif (setting_name[-4:] == "MULT" and value_name[:4] == "MUL_"):
        value_name = value_name[4:]
    elif (setting_name[-5:] == "WINSZ" and value_name[:6] == "WINSZ_"):
        value_name = value_name[6:]
    elif (setting_name[-3:] == "PWP" and value_name[:3] == "PWP"):
        value_name = value_name[3:]
    elif (setting_name[-2:] == "PS" and value_name[:2] == "PS"):
        value_name = value_name[2:]
    elif (setting_name[-3:] == "RNG" and value_name[:6] == "RANGE_"):
        value_name = value_name[6:]
    elif (setting_name[-4:] == "GAIN" and value_name[:5] == "GAIN_"):
        value_name = value_name[5:]
    elif (setting_name[-6:] == "DMTCNT" and value_name[:3] == "DMT"):
        value_name = value_name[3:]
    elif (setting_name[-5:] == "SMCLR" and value_name[:5] == "MCLR_"):
        value_name = value_name[5:]
    elif (setting_name == "ICESEL" and value_name[:4] == "ICS_"):
        value_name = value_name[4:]

    return setting_name + "_" + value_name

    
def read_configuration_data (file):

    cword = 4
    exp_line = re.compile ("([^:]+):([^:]+):([^:]+):(.*)")
    exp_ignore = re.compile ("^(A_|AUBA_|UBA_|ABF1_|BF1_|ABF2_|BF2_)")
    linenr = 0

    config = []
    section = {}

    fp = open (file, "r")

    if (fp == None):
        return None

    while 1:

        line = fp.readline().strip ()
        linenr += 1

        if (linenr == 1):
            if (line != "Daytona Configuration Word Definitions: 0001"):
                return None
            else:
                continue

        # EOF?
        if (line == ""):
            break

        parts = exp_line.match (line)

        if (parts):

            if (parts.group (1) == "CWORD"):

                cword -= 1
                if (cword < 0):
                    section = None
                    continue

                section = {}
                section['id'] = cword
                section['address'] = parts.group (2)
                section['mask'] = parts.group (3)
                section['default'] = parts.group (4)
                section['settings'] = []

                config.append (section)
                
            elif (parts.group (1) == "CSETTING"):
                
                if (section == None or exp_ignore.match (parts.group (3))):
                    setting = None
                    continue

                setting = {}
                setting['name'] = parts.group (3)
                setting['comment'] = parts.group (4)
                
                bits = int (parts.group (2), 16)
                bitspos = 0
                while ((bits & 1) == 0):
                    bits = bits >> 1
                    bitspos += 1

                setting['mask'] = bits
                setting['maskpos'] = bitspos
                setting['values'] = []

                section['settings'].append (setting)

            elif (parts.group (1) == "CVALUE"):

                if (setting == None):
                    continue
                    
                value = {}
                value['val'] = (int (parts.group (2), 16) >> setting['maskpos']) & setting['mask']
                value['name'] = parts.group (3)
                value['comment'] = parts.group (4)

                setting['values'].append (value)

        else:

            print "// Invalid line %d: %s" % (linenr, line)


    return config
    

def main (argv):

    config = read_configuration_data (argv[1])

    print "#ifndef __PIC32_CONFIG_H"
    print "#define __PIC32_CONFIG_H"
    print ""

    for section in config:
        print "#define CONFIG%d     const int __attribute__(( section(\".config_%s\") )) _config%d" % (section['id'], section['address'], section['id'])

    for section in config:
        print ""
        for setting in section['settings']:
            print "#define CONFIG%d_%s(val)%s (~((~(int)val & 0x%04X) << %02s) & 0x%s)" % (section['id'], setting['name'], " " * (10 - len (setting['name'])), setting['mask'], str (setting['maskpos']), section['mask'])
            

    for section in config:
        for setting in section['settings']:

            if (len (setting['values']) == 0):
                continue

            print ""
            print "typedef enum {"
            for value in setting['values']:
                valname = format_value_name (setting['name'], value['name'])
                print "    %s%s = %03s, // %s" % (valname, " " * (18 - len (valname)), str (value['val']), value['comment'])
            print "} config_%s_t;" % (setting['name'].lower ())

    print ""
    print "#endif // __PIC32_CONFIG_H"


if __name__ == "__main__":
    main (sys.argv)

