# Download finished game sgf and add previously saved assessments to sgf
import requests

class Sgf:
    def __init__(self, rootNode=None, headInfo=None, lastInfo=None):
        self.rootNode = rootNode
        self.headInfo = headInfo # string in sgf before first move
        self.lastInfo = lastInfo # string in sgf after last move
    def recursivePrintSgf(self, file):
        file.write(self.headInfo)
        self.rootNode.recursivePrintSgf(file)
        file.write(self.lastInfo)
    def depth(self):
        return self.rootNode.depth()
class SgfNode:
    def __init__(self, loc=None, color=None, comment=None):
        self.loc = loc
        self.color = color
        self.comment = comment
        self.children = []
    def recursivePrintSgf(self, file):
        if self.loc is not None:
            file.write(f';{self.color}[{self.loc}]')
        if self.comment is not None:
            file.write(f'C[{self.comment}]')
        if len(self.children) > 1:
            for child in self.children:
                file.write('(')
                child.recursivePrintSgf(file)
                file.write(')')
        elif len(self.children) == 1:
            self.children[0].recursivePrintSgf(file)
    def depth(self):
        if len(self.children) == 0:
            return 1
        else:
            return 1 + max([child.depth() for child in self.children])
def parseLocString(loc, boardSize):
    # 'ABCDEFGHJKLMNOPQRSTUVWXYZ' to 'abcdefghijklmnopqrstuvwxy'
    # boardSize~1 to 'abcdefghijklmnopqrstuvwxy'
    loc = loc.lower()
    x = loc[0]
    y = loc[1:]
    if ord('a') <= ord(x) <= ord('h'):
        pass
    elif ord('j') <= ord(x) <= ord('z'):
        x = chr(ord(x) - 1)
    else:
        raise Exception(f'Invalid loc string: {loc}')
    
    if y.isdigit() and 1 <= int(y) <= 25:
        y = chr(ord('a') + boardSize - int(y))
    else:
        raise Exception(f'Invalid loc string: {loc}')
    return x + y
def parseSgfLoc(s):
    # do not support parse comment
    # s looks like 'B[ab]'
    # return SgfNode
    if s[0] == 'B':
        color = 'B'
    elif s[0] == 'W':
        color = 'W'
    else:
        raise Exception(f'Invalid sgf loc string: {s}')
    loc = parseLocString(s[2:-1],19)
    return SgfNode(loc, color)

def parseSgf(s):
    # s is the content of sgf file
    # return Sgf object

    secondSemicolonIndex = s.find(";", s.find(";") + 1)
    #the line of the second semicolon looks like ";B[pd]" or ";MN[1]W[cn]"
    headInfo = s[:secondSemicolonIndex]
    lastInfo = ''
    s = s[secondSemicolonIndex:].splitlines()

    def parseLineLoc(line):
        line = line.strip(' ;')
        if line.startswith('MN'):
            line = line[line.find(']')+1:]
        if line.startswith('B') or line.startswith('W'):
            color = line[0]
        else:
            raise Exception(f'Invalid sgf loc string: {line}')
        assert line[1] == '[' and line[-1] == ']'
        loc = line[2:-1]
        assert len(loc) == 2 or len(loc) == 0
        if len(loc) == 2:
            assert loc[0].isalpha() and loc[1].isalpha()
        return SgfNode(loc, color)

    rootNode = parseLineLoc(s[0])
    lastNode = rootNode
    for i in range(1,len(s)):
        if s[i].startswith(';'):
            node = parseLineLoc(s[i])
            lastNode.children.append(node)
            lastNode = node
        else:
            lastInfo = '\n'.join(s[i:])
            break
    return Sgf(rootNode, headInfo, lastInfo)
def downloadsgf(id):
    url = f"https://www.dragongoserver.net/sgf.php?gid={id}&owned_comments=N"
    r = requests.get(url)
    sgf = parseSgf(r.text)
    return sgf
def readsgf(filename):
    with open(filename, 'r') as f:
        sgf = parseSgf(f.read())
    return sgf
def addInfo(sgf, info):
    # info = [{'winrate':'100', 'lead':'100', 'recommend':'Q16'},None,{...},...]
    node = sgf.rootNode
    for i in range(min(sgf.depth(), len(info))):
        if info[i] == None:
            node = node.children[0]
            continue
        cmt = ''
        if 'winrate' in info[i]:
            cmt += f'{info[i]["winrate"]}%'
        if 'lead' in info[i]:
            if cmt != '':
                cmt += ' '
            cmt += f'{info[i]["lead"]}'
        if 'recommend' in info[i]:
            loc = parseLocString(info[i]['recommend'],19)
            node.children.append(SgfNode(loc, node.children[0].color))
        node.comment = cmt
        node = node.children[0]
    return sgf

if __name__ == '__main__':
    sgf = readsgf('1421122.sgf')
    sgf = addInfo(sgf, [{'winrate':'100', 'lead':'100', 'recommend':'O17'},None,{'winrate':'100', 'lead':'100', 'recommend':'R14'}])
    with open('test.sgf', 'w') as f:
        sgf.recursivePrintSgf(f)