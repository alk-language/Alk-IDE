import wx
import wx.adv
import wx.lib.dialogs
import wx.lib.scrolledpanel
import wx.stc as stc
import subprocess
from subprocess import Popen, PIPE
import os
import re
from functools import partial
import sys, getopt
import json


GLOBAL_CMDS = []
INPUT_CMD = None
INPUT = ""
INPUT_INDEX = -1
WIN = False #imi dau seama daca rulez pe Windows sau nu / Linux/ MacOS
class CommAreaPos:
    def __init__(self, begin = -1, end = -1):
        self.begin = begin
        self.end = end


class Preferences(object):
    COMMENT_LINE, \
    COMMENT_AREA, \
    KEYWORDS, \
    DEFAULT_KEYWORDS, \
    METHODS, \
    NUMERIC, \
    STRINGS, \
    CHARS, \
    OPERATORS = range(9)
    def __init__(self):
        self.PrefsPath = "" #calea catre fisierul json in care retin toate preferintele
        self.AlkSyntax = {
            "AlkCommentLine" : [],
            "AlkCommentArea" : [],
            "AlkKeywords" : [],
            "AlkDefaultKeywords" : "",
            "AlkMethods" : [],
            "AlkNumeric" : [],
            "AlkStrings" : [],
            "AlkChars" : [],
            "AlkOperators" : []
        }
        self.ViewSettings = {
            "LineNumber" : True,
            "VerticalScrollBar" : True,
            "HorizontalScrollBar" : True,
            "StatusBar" : True,
            "Toolbar" : True,
            "ProjectsTab" : True
        }
        self.AlkSetup = {
            "SelectedAlkSetup" : -1, #ce index din AlkJarPathFiles am selectat
            "AlkJarPathFiles" : []
        }
    def LoadPrefs(self):
        self.OpenAlkSetup()
        self.OpenAlkSyntaxPrefs()
        self.OpenViewSettingsPrefs() #incarc toate preferintele din fisierele json
    def SetupCwd(self, path):
        self.PrefsPath = os.path.join(path, "Preferences")
    def SaveAlkSyntaxPrefs(self):
        f = open(os.path.join(self.PrefsPath , "AlkSyntaxPrefs.json"), "w")
        json.dump(self.AlkSyntax, f, indent = True)
        f.close()
    def OpenAlkSyntaxPrefs(self):
        f = open(os.path.join(self.PrefsPath , "AlkSyntaxPrefs.json"), "r")
        self.AlkSyntax = json.load(f)
        f.close()
    def SaveViewSettingPrefs(self):
        f = open(os.path.join(self.PrefsPath, "ViewSettings.json"), "w")
        json.dump(self.ViewSettings, f, indent = True)
        f.close()
    def OpenViewSettingsPrefs(self):
        f = open(os.path.join(self.PrefsPath, "ViewSettings.json"), "r")
        self.ViewSettings = json.load(f)
        f.close()
    def SaveAlkSetup(self):
        f = open(os.path.join(self.PrefsPath, "AlkSetup.json"), "w")
        json.dump(self.AlkSetup, f, indent = True)
        f.close()
    def OpenAlkSetup(self):
        f = open(os.path.join(self.PrefsPath, "AlkSetup.json"), "r")
        self.AlkSetup = json.load(f)
        f.close()

PREFERENCES = Preferences()

class KeywordLexer(object):
    def __init__(self):
        super(KeywordLexer, self)
    def StartStylingPlatform(self, buffer, startPos):
        if WIN:
            buffer.StartStyling(startPos, 31)
        else:
            buffer.StartStyling(startPos)
    def StyleText(self, event):
        buffer = event.EventObject
        lastStyled = buffer.GetEndStyled()
        #pt cuvinte intregi
        line = buffer.LineFromPosition(lastStyled)
        #caut comentariu pe linie 
        startPos = buffer.PositionFromLine(line)
        endPos = event.GetPosition()
        curWord = ""
        #prevChar = ''
        AreCifre = False # verific daca cuvantul curent are cifre 
        EsteIdentificator = False # daca are litere inseamna ca este identificator
        EsteString = False #verificam daca are string
        CommLinie = False #daca avem comentariu pe linie
        EsteChar = False # daca avem chars pe linie
        EsteOperator = False
        while startPos < endPos:
            if buffer.UpdateCommAreas(startPos) is True and not CommLinie and not EsteString and not EsteChar:
                self.StartStylingPlatform(buffer, startPos)
                buffer.SetStyling(1, PREFERENCES.COMMENT_AREA)
                startPos += 1
                continue
            char = chr(buffer.GetCharAt(startPos))
            
            if char.isspace() == False and char not in "()[}]{:;.,\\":
                curWord += char
                self.StartStylingPlatform(buffer, startPos)
                if char.isidentifier(): #daca am gasit vreo litera presupunem ca este un identificator
                    EsteIdentificator = True
                    if AreCifre:
                        AreCifre = False
                        curWord = char
                    if EsteOperator:
                        curWord = char
                        EsteOperator = False
                if char >= '0' and char <= '9': # inseamna ca are si cifre
                    AreCifre = True
                    if not EsteIdentificator:
                        curWord = char
                    if EsteOperator:
                        curWord = char
                        EsteOperator = False
                if char in PREFERENCES.AlkSyntax["AlkOperators"][1:]:
                    EsteOperator = True
                    if EsteIdentificator and not EsteString and not EsteChar:
                        EsteIdentificator = False
                        curWord = char

                if curWord == PREFERENCES.AlkSyntax["AlkCommentLine"][1] and not EsteChar: # am inceput comentariul
                    self.StartStylingPlatform(buffer, max(0, startPos - len(curWord) + 1))
                    CommLinie = True
                    buffer.SetStyling(len(curWord), PREFERENCES.COMMENT_LINE)
                elif char in PREFERENCES.AlkSyntax["AlkStrings"][1] and not CommLinie:
                    if EsteString: #daca deja am inceput cu string ul
                        EsteString = False
                        curWord = ""
                        startPos += 1
                        buffer.SetStyling(1, PREFERENCES.STRINGS)
                        continue
                    else:
                        EsteString = True #daca nu atunci inseamna ca acum a inceput stringul
                        buffer.SetStyling(1, PREFERENCES.STRINGS)
                elif char in PREFERENCES.AlkSyntax["AlkChars"][1] and not CommLinie and not EsteString:
                    if EsteChar:
                        EsteChar = False
                        curWord = ""
                        startPos += 1
                        buffer.SetStyling(1, PREFERENCES.CHARS)
                        continue
                    else:
                        EsteChar = True
                        buffer.SetStyling(1, PREFERENCES.CHARS)
                elif EsteChar:
                    buffer.SetStyling(len(curWord), PREFERENCES.CHARS)
                elif EsteString:
                    #print("da2")
                    buffer.SetStyling(len(curWord), PREFERENCES.STRINGS)
                elif CommLinie:
                    buffer.SetStyling(1, PREFERENCES.COMMENT_LINE)
                elif EsteIdentificator: # presupunem ca este identificator , verificam daca corespunde cu vreun element din sintaxa limbajului, daca nu , atunci este identificator
                    self.StartStylingPlatform(buffer, max(0, startPos - len(curWord) + 1))
                    #print("da4")                    
                    if AreCifre:
                        #print("da5")
                        buffer.SetStyling(len(curWord), PREFERENCES.DEFAULT_KEYWORDS)
                    elif curWord in PREFERENCES.AlkSyntax["AlkKeywords"][1:]:
                        #print("da6")
                        buffer.SetStyling(len(curWord), PREFERENCES.KEYWORDS)
                    elif curWord in PREFERENCES.AlkSyntax["AlkMethods"][1:]:
                        buffer.SetStyling(len(curWord), PREFERENCES.METHODS)
                        #print("da7")
                    elif curWord in PREFERENCES.AlkSyntax["AlkNumeric"][1:]:
                        #print("da8")
                        buffer.SetStyling(len(curWord), PREFERENCES.NUMERIC)
                    else:#atunci chiar este identificator
                        #print("da9")
                        buffer.SetStyling(len(curWord), PREFERENCES.DEFAULT_KEYWORDS)
                else:
                    #print("da10")
                    if EsteOperator:
                        buffer.SetStyling(len(curWord), PREFERENCES.OPERATORS)
                    else:
                        buffer.SetStyling(len(curWord), PREFERENCES.NUMERIC)
            else:
                self.StartStylingPlatform(buffer, startPos)
                if not EsteString and not CommLinie and not EsteChar:
                    buffer.SetStyling(1, PREFERENCES.DEFAULT_KEYWORDS)
                elif EsteString and not CommLinie and not EsteChar:
                    buffer.SetStyling(len(curWord), PREFERENCES.STRINGS)
                elif EsteChar and not EsteString and not CommLinie:
                    buffer.SetStyling(1, PREFERENCES.CHARS)
                else:
                    buffer.SetStyling(1, PREFERENCES.COMMENT_LINE)
                if char == '\n':
                    if CommLinie:
                        CommLinie = False
                    if EsteString:
                        EsteString = False
                    if EsteChar:
                        EsteChar = False
                AreCifre = False 
                EsteIdentificator = False
                EsteOperator = False
                if not EsteString or not EsteChar:
                    curWord = ""
            #prevChar = char
            startPos += 1

class KeywordSTC(stc.StyledTextCtrl):
    def __init__(self, parent, style = wx.TE_MULTILINE | wx.TE_WORDWRAP | wx.TE_RICH | wx.NO_BORDER):
        super(KeywordSTC, self).__init__(parent, style = style)
        self._lexer = None
        #self.SetUseHorizontalScrollBar(False)
        self.SetFocus()
        self.SetTabWidth(12)
        #self.p = wx.Panel(self, size = (30, 30), pos = (40, 30)) pentru autocomplete
        self.Bind(stc.EVT_STC_STYLENEEDED, self.OnStyle)
        self.Bind(wx.EVT_KEY_UP, self.Intenteaza)
        self.Bind(wx.EVT_KEY_DOWN, self.IntenteazaEnter)
    def UpdateCommAreas(self, poz):
        self.CommAreas = []
        v = self.GetValue()
        lg = len(v)
        dim = 0
        i = 0
        while i < lg:
            pos = v.find(PREFERENCES.AlkSyntax["AlkCommentArea"][1], i)
            if pos != -1:
                i = pos + 1
                dim += 1
                self.CommAreas.append(CommAreaPos(pos, -1))
            else:
                break
        i = 0
        dim2 = 0
        while i < lg:
            pos = v.find(PREFERENCES.AlkSyntax["AlkCommentArea"][2], i)
            if pos != -1:
                i = pos + 1
                if dim2 < dim :
                    self.CommAreas[dim2].end = pos + 1
                dim2 += 1
            else:
                break
        for j in range(dim):
            if poz >= self.CommAreas[j].begin:
                if poz <= self.CommAreas[j].end or self.CommAreas[j].end == -1:
                    return True
        return False

    def IntenteazaEnter(self, e):
        code = e.GetKeyCode()
        if code == 13:
            nrTabs = self.GetLineIndentation(self.GetCurrentLine()) / self.GetTabWidth()
            strin = "\n"
            while nrTabs > 0:
                strin += '\t'
                nrTabs -= 1
            self.AddText(strin)
        else:
            e.Skip()

    def Intenteaza(self, e): #daca apas o tasta vreau sa verific ce tasta si daca este un  brackets sa le deschid
        char = chr(self.GetCharAt(self.GetCurrentPos() - 1))
        cheie = e.GetKeyCode()
        if cheie == 91 and char == '{': # daca e acolada deschisa
            nrTabs = self.GetLineIndentation(self.GetCurrentLine()) / self.GetTabWidth()
            subTabs = nrTabs + 1
            self.AddText('\n')
            while subTabs > 0:
                self.AddText('\t')
                subTabs -= 1
            subTabs = nrTabs + 1
            self.AddText('\n')
            while nrTabs > 0:
                self.AddText('\t')
                nrTabs -= 1
            self.AddText('}')
            self.CharLeft()
            while subTabs > 0:
                self.CharLeft()
                subTabs -= 1
        elif cheie == 57 and char == '(': #daca e paranteza deschisa
            self.AddText(")")
            self.CharLeft()
        elif cheie == 91 and char == '[': #daca e paranteza patrata
            self.AddText("]")
            self.CharLeft()
    def OnStyle(self, event):
        if self._lexer:
            self._lexer.StyleText(event)
        else:
            event.skip()
    
    def SetLexer(self, lexerID):
        if lexerID == stc.STC_LEX_CONTAINER:
            self._lexer = KeywordLexer()
        super(KeywordSTC, self).SetLexer(lexerID)






class TextPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.LiniiCod = KeywordSTC(self)
        self.CurentTab = None #referinta la tabloul deschis
        self.LiniiCod.MarkerDefine(1, stc.STC_MARK_ROUNDRECT , (220,0,0), (240,0,0)) # markerul 1 este cel de eroare
        self.LiniiCod.StyleSetBackground(stc.STC_STYLE_DEFAULT, (40, 70, 107)) # culoarea de fundal
        self.LiniiCod.StyleSetForeground(stc.STC_STYLE_DEFAULT, (0, 0, 0))
        self.LiniiCod.StyleClearAll()
        fontScris = wx.Font(20, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        self.LiniiCod.StyleSetFont(stc.STC_STYLE_LINENUMBER, fontScris)
        self.LiniiCod.StyleSetForeground(stc.STC_STYLE_LINENUMBER, (102, 148, 255))
        self.LiniiCod.StyleSetBackground(stc.STC_STYLE_LINENUMBER, (50, 80, 117))
        self.LiniiCod.SetMarginType(1, stc.STC_MARGIN_NUMBER) # pun numarul corespunzator fiecarei linii
        self.LiniiCod.SetMarginRight(5)
        self.LiniiCod.SetMarginLeft(5)
        self.LiniiCod.SetMarginWidth(1, 40) # latimea marginii din stanga(cea in care sunt numerele liniilor)
        x = range(11)
        for n in x:
            self.LiniiCod.StyleSetFont(n, fontScris)
        self.sizer = wx.BoxSizer()
        self.sizer.Add(self.LiniiCod, 1, wx.EXPAND)
        self.SetSizerAndFit(self.sizer)
        self.textTabsRef = None
        self.LiniiCod.Bind(wx.EVT_CHAR, self.Modificat)
    def InitTabRef(self, ref):
        self.CurentTab = ref
    def Modificat(self, e):
        if self.CurentTab.Saved:
           v = self.CurentTab
           v.MarkAsUnsaved()
        e.Skip()

class ButtonTab(wx.Button):

    def __init__(self, parent, label):
        wx.Button.__init__(self, parent, label = label, style = wx.NO_BORDER, size = (60, -1))
        self.SetBackgroundColour((25, 65, 94))
        self.SetForegroundColour((255, 255, 255))
class CloseButtonTab(wx.Button):

    def __init__(self, parent, label):
        wx.Button.__init__(self, parent, label = label, style = wx.NO_BORDER, size = (10, -1))
        self.SetBackgroundColour((25, 65, 94))
        self.SetForegroundColour((255, 255, 255))
class Tab(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, size = (100, -1))
        self.index = -1
        self.FilePath = ""
        self.CarretPos = 0 #fiecare tab are propria pozitie a cursorului
        self.zoomLevel = 0 #fiecare tab are nivelul de zoom
        self.TmpCnt = "" #pentru fisierele ce nu vor fi salvate se va aloca un string in care se va retine continutul fiecarui tab
        self.Saved = False #daca am salvat vreodata
        self.FileName = "Untitled"
        self.CodeTextRef = parent.TextPanelReference # salvez in fiecare panel referinta la partea de inserat codul
        self.buttonTab = ButtonTab(self, "*Untitled")
        self.buttonClose = CloseButtonTab(self, "x")
        self.hbsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hbsizer.Add(self.buttonTab, 3, wx.EXPAND)
        self.hbsizer.Add(self.buttonClose, 0, wx.EXPAND)
        self.SetSizer(self.hbsizer)
    def SetFilePath(self, path):
        self.FilePath = path
    def SetFileName(self, name):
        self.FileName = name
        self.buttonTab.SetLabelText(name)
        self.buttonTab.Refresh()
    def MarkAsUnsaved(self):
        self.buttonTab.SetLabelText('*' + self.FileName)
        self.buttonTab.Refresh()
        self.Saved = False
    def MarkAsSaved(self):
        self.buttonTab.SetLabelText(self.FileName)
        self.buttonTab.Refresh()
        self.Saved = True
class TextTabs(wx.Panel):
    def __init__(self, parent, textPanel):
        wx.Panel.__init__(self, parent)
        self.tabs = []
        self.TextPanelReference = textPanel #referinta la panelul cu text
        self.SetBackgroundColour((55, 85, 125))
        self.gridsizer = wx.FlexGridSizer(1,0,0,3)
        self.gridsizer.Add(Tab(self), 0)
        #self.tabs[1].GetWindow().buttonTab.SetBackgroundColour((23,44,124))
        self.SetSizer(self.gridsizer)
        self.UpdateTabList()
        self.CurrentTab = -1 #tabul care este deschis curent
        self.SelectTab(None, 0, False)
    def AreSavedAll(self):
        for tab in self.tabs:
            tabb = tab.GetWindow()
            if not tabb.Saved:
                return False
        return True
    def SaveAll(self):
        i = 0
        for tab in self.tabs:
            tabb = tab.GetWindow()
            if tabb.Saved: #inseamna ca are  o locatie pe disk si poate fi salvat
                f = open(os.path.join(tabb.FilePath, tabb.FileName), 'w')
                f.write(self.TextPanelReference.LiniiCod.GetValue())
                tabb.MarkAsSaved()
                f.close()
            elif len(tabb.FilePath) == 0:
                i += 1
        return i
    def UpdateTabList(self):
        self.tabs = self.gridsizer.GetChildren()
        i = 0
        while i < len(self.tabs):
            tab = self.tabs[i].GetWindow()
            tab.index = i
            tab.buttonClose.Bind(wx.EVT_BUTTON, partial( self.CloseTab, index = i ) ) 
            tab.buttonTab.Bind(wx.EVT_BUTTON, partial( self.SelectTab, index = i, unselect = True ) ) 
            i += 1 
        self.Layout()
    def CloseTab(self, e, index):
        self.gridsizer.Hide(index)
        self.gridsizer.Remove(index)
        self.UpdateTabList()
        if len(self.tabs) > 0 and index == self.CurrentTab:
            self.SelectTab(None, 0, False)
        elif len(self.tabs) > 0:
            self.CurrentTab -= 1
        else:
            self.TextPanelReference.LiniiCod.SetValue("")
            self.TextPanelReference.LiniiCod.SetEditable(False)
            #aici cod cand am inchis toate tab urile
    def AddTab(self, path, fileName, created):
        if len(self.tabs) == 0:
            self.TextPanelReference.LiniiCod.SetEditable(True)
        tab = Tab(self)
        self.gridsizer.Add(tab, 0)
        self.UpdateTabList()
        if not created:
            tab.SetFileName(fileName)
            tab.SetFilePath(path)
            tab.Saved = True
        self.SelectTab(None, tab.index, True)
        
    def UnselectTab(self, index):
        if self.CurrentTab > -1: # deselectez tabul de dinainte
            tab = self.tabs[self.CurrentTab].GetWindow()
            if not tab.Saved:
                tab.TmpCnt = self.TextPanelReference.LiniiCod.GetValue()
            tab.CarretPos = self.TextPanelReference.LiniiCod.GetCurrentPos()
            tab.zoomLevel = self.TextPanelReference.LiniiCod.GetZoom() #iau nivelul de zoom precedent
            tab.buttonTab.SetBackgroundColour((25, 65, 94))
            tab.buttonClose.SetBackgroundColour((25, 65, 94))
    def SelectTab(self, e, index, unselect):
        if unselect:
            self.UnselectTab(self.CurrentTab)
        tab = self.tabs[index].GetWindow()
        self.TextPanelReference.CurentTab = tab
        tab.buttonTab.SetBackgroundColour((40, 70, 107))
        tab.buttonClose.SetBackgroundColour((40, 70, 107))
        if tab.Saved:
            f = open(os.path.join(tab.FilePath, tab.FileName), 'r')
            self.TextPanelReference.LiniiCod.SetValue(f.read())
            f.close()
        else:
            self.TextPanelReference.LiniiCod.SetValue(tab.TmpCnt)
        self.TextPanelReference.LiniiCod.SetFocus()
        self.TextPanelReference.LiniiCod.GotoPos(tab.CarretPos) #pastrez si pozitia cursorului de dinainte
        self.TextPanelReference.LiniiCod.SetZoom(tab.zoomLevel)#la fel si cu zoom ul
        self.TextPanelReference.LiniiCod.EmptyUndoBuffer()
        self.TextPanelReference.LiniiCod.SetUndoCollection(True)
        self.CurrentTab = index
class CommandInput(wx.TextCtrl):
    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style = wx.TE_RICH | wx.NO_BORDER, size = (-1, 30), value = "Enter command here:")
        self.SetFont(wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Lucida Console' ))
        self.ConsolaRef = self.GetParent()
        self.SetBackgroundColour((30,30,30))
        self.SetForegroundColour((255,255,255))
        self.introdus = False
        self.Bind(wx.EVT_SET_FOCUS, self.IntroduceCmd)
        self.Bind(wx.EVT_KILL_FOCUS, self.Deselecteaza)
        self.Bind(wx.EVT_KEY_UP, self.IntroduCmd)
    def IntroduceCmd(self, e):
        if not self.introdus:
            self.SetValue("")
            self.introdus = True
        e.Skip()
    def Deselecteaza(self, e):
        if len(self.GetValue().strip()) == 0:
            self.SetValue("Enter command here:")
            self.introdus = False
        e.Skip()
    def IntroduCmd(self, e):
        key = e.GetKeyCode()
        if key == 13:
            arg = self.GetValue()
            if len(arg.strip()) > 0 and not self.ConsolaRef.ApasatPeInput:
                tip = ""
                tip = arg[0] + arg[1]
                self.ConsolaRef.TextConsola.AppendText("Command argument " + '"' + arg + '"' + ' added to the command list. To see the command list go to Code>Add command.\n')                   
            GLOBAL_CMDS.append(arg)
            self.SetValue("")
class Consola(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.TextConsola = wx.TextCtrl(self, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH | wx.NO_BORDER)
        self.TextConsola.SetBackgroundColour((0,0,0))
        self.TextConsola.SetDefaultStyle(wx.TextAttr(wx.WHITE,wx.BLACK,font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Lucida Console' ))) #culoarea textului
        self.ApasatPeInput = False
        self.CmdInput = CommandInput(self)
        bsizer = wx.BoxSizer(wx.VERTICAL)
        bsizer.Add(self.TextConsola, 1, wx.EXPAND)
        bsizer.Add(self.CmdInput, 0, wx.EXPAND)
        self.SetSizerAndFit(bsizer)
        self.TextConsola.Bind(wx.EVT_KEY_DOWN, self.DelimitBackSpace)
        self.TextConsola.Bind(wx.EVT_KEY_UP, self.Scrie)
    def DelimitBackSpace(self, e):
        key = e.GetKeyCode()
        pos = self.TextConsola.GetInsertionPoint()
        if key == 8:
            if pos > 21:
                e.Skip()
        else:
            e.Skip()
    def Scrie(self, e):
        global INPUT
        INPUT = self.TextConsola.GetValue()[21:]
    def Eroare(self, mesaj):
        self.TextConsola.SetDefaultStyle(wx.TextAttr(wx.RED,wx.BLACK,font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Lucida Console' ))) #culoarea textului
        self.TextConsola.AppendText(mesaj)
        self.TextConsola.SetDefaultStyle(wx.TextAttr(wx.WHITE,wx.BLACK,font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Lucida Console' ))) #culoarea textului
    def Input(self, e):
        self.TextConsola.SetFocus()
        self.TextConsola.SetFont(wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Lucida Console' ))
        self.TextConsola.SetForegroundColour((255,255,255))
        self.TextConsola.SetEditable(True)
        self.ApasatPeInput = True # daca am deschis consola pt input
        self.TextConsola.SetValue("")
        self.TextConsola.WriteText("Request user input: \n" + INPUT)

class TopPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.text = TextPanel(self)
        self.textTabs = TextTabs(self, self.text)
        self.text.InitTabRef(self.textTabs.tabs[0].GetWindow())
        main_sizer.Add(self.textTabs, 0, wx.EXPAND)
        main_sizer.Add(self.text, 2, wx.EXPAND)
        self.consola = Consola(self)
        main_sizer.Add(self.consola, 1, wx.EXPAND)
        self.SetSizer(main_sizer)

#prin intermediul acestei clase am sa 'vizualizez' comenzile in ui
class CommandUI(wx.Panel):
    def __init__(self, parent,CmdString):
        wx.Panel.__init__(self, parent)
        self.CmdRef = None # referinta la tabela de comenzi din memorie
        Vsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.cmdUi = wx.StaticBox(self, label = CmdString) #textul in care se va vedea comanda
        self.removeCmdBtn = wx.Button(self, label = "X", style = wx.NO_BORDER, size = (30, -1))
        Vsizer.Add(self.cmdUi, 10, wx.EXPAND)
        Vsizer.Add(self.removeCmdBtn, 1, wx.EXPAND)
        self.SetSizerAndFit(Vsizer)
        self.removeCmdBtn.Bind(wx.EVT_BUTTON, self.RemoveCmd)
    def RemoveCmd(self, e):
        global INPUT_INDEX
        global INPUT_CMD
        global INPUT
        index = GLOBAL_CMDS.index(self.CmdRef)
        if index == INPUT_INDEX:
            INPUT_CMD = None
            INPUT = ""
            INPUT_INDEX = -1
        GLOBAL_CMDS.remove(self.CmdRef)
        del(self.CmdRef)
        self.CmdRef = None
        del(self.CmdRef)
        p =  self.GetParent()
        self.Destroy()
        p.Layout()

class CmdDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent)
        MainSizer = wx.BoxSizer(wx.VERTICAL)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        AddBtn = wx.Button(self, label = "Add")
        self.CmdInput = wx.TextCtrl(self, size = (200, -1))
        hsizer.Add(self.CmdInput, 1, wx.EXPAND)
        hsizer.Add(AddBtn, 0, wx.EXPAND)
        text = wx.StaticBox(self, label = "Add a command:")
        self.ScrollPanel = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.ScrollPanel.SetBackgroundColour((230,230,230))
        self.ScrollPanel.SetSizer(self.vsizer)
        #actualizez tabela cu toate comenzile salvate din memorie
        for cmd in GLOBAL_CMDS:
            NewCmd = CommandUI(self.ScrollPanel, cmd)
            NewCmd.CmdRef = cmd
            self.vsizer.Add(NewCmd, 0, wx.ALIGN_CENTER)
        MainSizer.Add(self.ScrollPanel, 3, wx.EXPAND)
        MainSizer.AddSpacer(10)
        MainSizer.Add(text, 0, wx.ALIGN_CENTER)
        MainSizer.Add(hsizer, 0, wx.ALIGN_CENTER)
        MainSizer.AddSpacer(20)
        self.SetSizer(MainSizer)
        self.SetTitle("Command List")
        AddBtn.Bind(wx.EVT_BUTTON , self.Add)
    def AddCmdUI(self, cmd):
        NewCmd = CommandUI(self.ScrollPanel, cmd)
        self.vsizer.Add(NewCmd, 0, wx.ALIGN_CENTER)
        NewCmd.CmdRef = GLOBAL_CMDS[len(GLOBAL_CMDS) - 1]
        self.vsizer.Layout()
        self.ScrollPanel.SetupScrolling()
    def Add(self, e):
        inputString = self.CmdInput.GetValue()
        if len(inputString.split()) > 0:    # apelez split sa scap de white space uri
            GLOBAL_CMDS.append(inputString)
            self.AddCmdUI(inputString)
            self.CmdInput.SetValue("")


class AlkPathFileUI(wx.Panel):#fiecare segment din sectiunea de set up a path ului catre executabilul alk

    def __init__(self, parent, path, dialogRef):
        wx.Panel.__init__(self, parent)
        self.index = -1
        self.FilePath = path
        self.DialogRef = dialogRef
        self.buttonPath = wx.Button(self, label = path , style = wx.NO_BORDER, size = (350, -1))
        self.buttonClose = wx.Button(self, label = "X", style = wx.NO_BORDER)
        self.buttonPath.SetBackgroundColour((200 , 200 , 200))
        self.buttonClose.SetBackgroundColour((200 , 220 , 220))
        hbsizer = wx.BoxSizer(wx.HORIZONTAL)
        hbsizer.Add(self.buttonPath, 4, wx.EXPAND)
        hbsizer.Add(self.buttonClose, 1, wx.EXPAND)
        self.SetSizer(hbsizer)
        self.buttonPath.Bind(wx.EVT_BUTTON, self.SelectPath)
        self.buttonClose.Bind(wx.EVT_BUTTON, self.RemovePath)
    def RemovePath(self, e):
        p = self.GetParent()
        ref = self.DialogRef
        del(ref.paths[self.index])
        if self.index < PREFERENCES.AlkSetup["SelectedAlkSetup"]:
            PREFERENCES.AlkSetup["SelectedAlkSetup"] = PREFERENCES.AlkSetup["SelectedAlkSetup"] - 1
        elif self.index == PREFERENCES.AlkSetup["SelectedAlkSetup"]:
            PREFERENCES.AlkSetup["SelectedAlkSetup"] = -1
        del(PREFERENCES.AlkSetup["AlkJarPathFiles"][self.index])
        i = 0
        for path in ref.paths:
            path.index = i
            i += 1
        self.Destroy()
        p.Layout()
    def SelectPath(self, e):
        if PREFERENCES.AlkSetup["SelectedAlkSetup"] > -1:
            self.DialogRef.paths[PREFERENCES.AlkSetup["SelectedAlkSetup"]].UnselectPath()
        PREFERENCES.AlkSetup["SelectedAlkSetup"] = self.index
        self.buttonPath.SetBackgroundColour((191, 255, 168))
        self.buttonClose.SetBackgroundColour((191, 230, 188))
    def UnselectPath(self):
        self.buttonPath.SetBackgroundColour((200 , 200 , 200))
        self.buttonClose.SetBackgroundColour((200 , 220 , 220))

class AlkSetupDialog(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, size = (500, -1))
        self.paths = []
        MainSizer = wx.BoxSizer(wx.VERTICAL)
        self.vsizer = wx.BoxSizer(wx.VERTICAL)
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        BrowseBtn = wx.Button(self, label = "Browse")
        AddBtn = wx.Button(self, label = "Add")
        self.PathInput = wx.TextCtrl(self, size = (200, -1))
        hsizer.Add(self.PathInput, 1, wx.EXPAND)
        hsizer.Add(BrowseBtn, 0, wx.EXPAND)
        hsizer.Add(AddBtn, 0, wx.EXPAND)
        text = wx.StaticBox(self, label = "Add path:")
        self.ScrollPanel = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.ScrollPanel.SetBackgroundColour((230,230,230))
        self.ScrollPanel.SetSizer(self.vsizer)
        #actualizez tabela cu toate path-urile salvate din memorie

        MainSizer.Add(self.ScrollPanel, 3, wx.EXPAND)
        MainSizer.AddSpacer(10)
        MainSizer.Add(text, 0, wx.ALIGN_CENTER)
        MainSizer.Add(hsizer, 0, wx.ALIGN_CENTER)
        MainSizer.AddSpacer(20)
        self.SetSizer(MainSizer)
        self.SetTitle("Setup your alk jar executable")
        AddBtn.Bind(wx.EVT_BUTTON , self.Add)
        BrowseBtn.Bind(wx.EVT_BUTTON , self.BrowsePath)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        paths = PREFERENCES.AlkSetup["AlkJarPathFiles"]
        i = 0
        selected = PREFERENCES.AlkSetup["SelectedAlkSetup"]
        for path in paths:
            NewPath = AlkPathFileUI(self.ScrollPanel, path, self)
            self.paths.append(NewPath)
            NewPath.index = len(self.paths) - 1
            self.vsizer.Add(NewPath, 0, wx.ALIGN_CENTER)
            if i == selected:
                NewPath.SelectPath(None)
            i += 1
    def AddAlkPath(self, path):
        NewPath = AlkPathFileUI(self.ScrollPanel, path, self)
        self.paths.append(NewPath)
        NewPath.index = len(self.paths) - 1
        self.vsizer.Add(NewPath, 0, wx.ALIGN_CENTER)
        self.vsizer.Layout()
        self.ScrollPanel.SetupScrolling()
    def Add(self, e):
        inputString = self.PathInput.GetValue()
        if len(inputString.split()) > 0:    # apelez split sa scap de white space uri
            self.AddAlkPath(inputString)
            self.PathInput.SetValue("")
            PREFERENCES.AlkSetup["AlkJarPathFiles"].append(inputString)
    def OnClose(self, e):
        PREFERENCES.SaveAlkSetup()
        self.Destroy()
    def BrowsePath(self, e):
        try:
            casuta = wx.FileDialog(self, "Choose alk jar executable...", os.getcwd(), "", "*.jar*", wx.FD_OPEN)
            if casuta.ShowModal() == wx.ID_OK:
                self.PathInput.SetValue(os.path.join(casuta.GetDirectory(), casuta.GetFilename()))
            casuta.Destroy()
        except:
            casuta = wx.MessageDialog(self, "Couldn't open the specified file.", "Error", wx.ICON_ERROR)
            casuta.ShowModal()
            casuta.Destroy()
class FindDialog(wx.Dialog):
    def __init__(self, parent, CodePart):
        wx.Dialog.__init__(self, parent)
        self.CodePart = CodePart
        self.SetSize((250, 200))
        self.SetTitle("Find a specific text")
        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(pnl, label='Insert text to find:')
        sbs = wx.StaticBoxSizer(sb, orient=wx.VERTICAL)

        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.Searchbox = wx.TextCtrl(pnl)
        hbox1.Add(self.Searchbox, flag=wx.LEFT, border=5)
        sbs.Add(hbox1)

        pnl.SetSizer(sbs)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        FindBtn = wx.Button(self, label='Find')
        closeButton = wx.Button(self, label='Close')
        hbox2.Add(FindBtn)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(pnl, proportion=1,
            flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)

        FindBtn.Bind(wx.EVT_BUTTON, self.FindText)
        closeButton.Bind(wx.EVT_BUTTON, self.OnClose)

    def FindText(self, e):
        self.CodePart.SetSelection(-1,0)
        if len(self.Searchbox.GetValue()) > 0:
            sir = self.CodePart.GetValue()
            lg = len(sir)
            sir2 = self.Searchbox.GetValue()
            sze = len(sir2)
           # nr = 0
            i = 0
            while i < lg:
                pos = sir.find(sir2, i)
                if pos != -1:
                    i = pos + sze
                    #nr += 1 # aici pot implementa un go next sau ceva pe viitor
                    self.CodePart.AddSelection(pos, i)
                else:
                    break
            self.Destroy()
    def OnClose(self, e):

        self.Destroy()

class ReplaceDialog(wx.Dialog):
    def __init__(self, parent, CodePart):
        wx.Dialog.__init__(self, parent)
        self.CodePart = CodePart
        self.SetSize((250, 200))
        self.SetTitle("Replace a specific text")
        pnl = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)
        sizer_panel = wx.BoxSizer(wx.VERTICAL)
        sizer_elem = wx.BoxSizer(wx.HORIZONTAL)
        text1 = wx.StaticText(pnl, id = wx.ID_ANY, label =" Find text: " )
        self.Searchbox = wx.TextCtrl(pnl)
        sizer_elem.Add(text1)
        sizer_elem.Add(self.Searchbox)
        sizer_elem2 = wx.BoxSizer(wx.HORIZONTAL)
        text2 = wx.StaticText(pnl, id = wx.ID_ANY, label =" Replace with: " )
        sizer_elem2.Add(text2)
        self.Replacebox = wx.TextCtrl(pnl)
        sizer_elem2.Add(self.Replacebox)
        sizer_panel.Add(sizer_elem, 0, wx.BOTTOM, 25)
        sizer_panel.Add(sizer_elem2, 0, wx.BOTTOM, 5)
        pnl.SetSizer(sizer_panel)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        FindBtn = wx.Button(self, label='Replace')
        closeButton = wx.Button(self, label='Close')
        hbox2.Add(FindBtn)
        hbox2.Add(closeButton, flag=wx.LEFT, border=5)

        vbox.Add(pnl, proportion=1,
            flag=wx.ALL|wx.EXPAND, border=5)
        vbox.Add(hbox2, flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        self.SetSizer(vbox)

        FindBtn.Bind(wx.EVT_BUTTON, self.FindText)
        closeButton.Bind(wx.EVT_BUTTON, self.OnClose)

    def FindText(self, e):
        self.CodePart.SetSelection(-1,0)
        if len(self.Searchbox.GetValue()) > 0 and len(self.Replacebox.GetValue()) > 0:
            sir = self.CodePart.GetValue()
            lg = len(sir)
            sir2 = self.Searchbox.GetValue()
            sze = len(sir2)
           # nr = 0
            i = 0
            while i < lg:
                pos = sir.find(sir2, i)
                if pos != -1:
                    i = pos + sze
                    #nr += 1 # aici pot implementa un go next sau ceva pe viitor
                    self.CodePart.AddSelection(pos, i)
                    self.CodePart.ReplaceSelection(self.Replacebox.GetValue())
                else:
                    break
            self.Destroy()
    def OnClose(self, e):

        self.Destroy()

class FereastraPrincipala(wx.Frame):
    def __init__(self, parinte, titlu, argv):
        fontScris = wx.Font(20, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas' ) # fontul in care o sa fie scris codul
        fontConsola = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Lucida Console' ) # fontul in care o sa fie scris consola
        self.numeFisier  = ''
        self.prefsModified = False
        self.numeDirector, self.numeFisier = os.path.split(str(argv[0]))
        if len(self.numeDirector.split()) == 0:
            self.numeDirector = os.getcwd()
        PREFERENCES.SetupCwd(self.numeDirector)
        self.tmpDir = os.path.join(self.numeDirector, "tmp")
        self.markereErori = []
        PREFERENCES.LoadPrefs()
        wx.Frame.__init__(self, parinte, title = titlu, size = (800, 600))
        self.panel = TopPanel(self)
        self.CodePart = self.panel.text.LiniiCod
        self.CodePart.SetLexer(stc.STC_LEX_CONTAINER)
        self.CodePart.StyleSetSpec(PREFERENCES.DEFAULT_KEYWORDS, "fore:" + PREFERENCES.AlkSyntax["AlkDefaultKeywords"])
        self.CodePart.StyleSetSpec(PREFERENCES.KEYWORDS, "fore:" + PREFERENCES.AlkSyntax["AlkKeywords"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.METHODS, "fore:" + PREFERENCES.AlkSyntax["AlkMethods"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.OPERATORS, "fore:" + PREFERENCES.AlkSyntax["AlkOperators"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.NUMERIC, "fore:" + PREFERENCES.AlkSyntax["AlkNumeric"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.COMMENT_LINE, "fore:" + PREFERENCES.AlkSyntax["AlkCommentLine"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.STRINGS, "fore:" + PREFERENCES.AlkSyntax["AlkStrings"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.COMMENT_AREA, "fore:" + PREFERENCES.AlkSyntax["AlkCommentArea"][0])
        self.CodePart.StyleSetSpec(PREFERENCES.CHARS, "fore:" + PREFERENCES.AlkSyntax["AlkChars"][0])
        self.panel.consola.Hide()
        self.CreateStatusBar()

        self.toolBar = self.CreateToolBar(wx.NO_BORDER | wx.TB_FLAT | wx.TB_NODIVIDER)
        self.toolBar.SetBackgroundColour((50,80,110))
        SaveFile = self.toolBar.AddTool(wx.ID_ANY, "Save File", wx.Bitmap(self.numeDirector +"/bitmaps/SaveFile.png"))
        NewFile = self.toolBar.AddTool(wx.ID_ANY, "New File", wx.Bitmap(self.numeDirector +"/bitmaps/NewFile.png"))
        OpenFile = self.toolBar.AddTool(wx.ID_ANY, "Open File", wx.Bitmap(self.numeDirector +"/bitmaps/OpenFile.png"))
        self.toolBar.AddSeparator()
        Undo = self.toolBar.AddTool(wx.ID_UNDO, "Undo", wx.Bitmap(self.numeDirector +"/bitmaps/Undo.png"))
        Redo = self.toolBar.AddTool(wx.ID_REDO, "Redo", wx.Bitmap(self.numeDirector +"/bitmaps/Redo.png"))
        self.toolBar.AddSeparator()
        ShowConsole = self.toolBar.AddTool(wx.ID_ANY, "Toggle Console On/Off", wx.Bitmap(self.numeDirector +"/bitmaps/ShowConsole.png"))
        CloseConsole = self.toolBar.AddTool(wx.ID_ANY, "Toggle Console On/Off", wx.Bitmap(self.numeDirector +"/bitmaps/CloseConsole.png"))
        Run = self.toolBar.AddTool(wx.ID_EXECUTE, "Run program", wx.Bitmap(self.numeDirector +"/bitmaps/Run.png"))
        CmdList = self.toolBar.AddTool(wx.ID_ANY, "Open commands list", wx.Bitmap(self.numeDirector +"/bitmaps/Cmd.png"))
        self.toolBar.Realize()
        self.Bind(wx.EVT_TOOL, self.OpenCmdMenu, CmdList)
        self.Bind(wx.EVT_TOOL, self.RuleazaProgramul, Run)
        self.Bind(wx.EVT_TOOL, lambda event: self.DeschideConsola(True), ShowConsole)
        self.Bind(wx.EVT_TOOL, lambda event: self.InchideConsola(), CloseConsole)
        self.Bind(wx.EVT_TOOL, self.FaUndo, Undo)
        self.Bind(wx.EVT_TOOL, self.FaRedo, Redo)
        self.Bind(wx.EVT_TOOL, self.FisierNou, NewFile)
        self.Bind(wx.EVT_TOOL, self.DeschideFisier, OpenFile)
        self.Bind(wx.EVT_TOOL, self.SalveazaFisier, SaveFile)
        self.StatusBar.SetBackgroundColour((50, 80, 117)) # albastru inchis
        #butoanele din bara de sus
        FileMeniu = wx.Menu()
        EditMeniu = wx.Menu()
        SelectMeniu = wx.Menu()
        ViewMeniu = wx.Menu()
        CodeMeniu = wx.Menu()
        SettingsMeniu = wx.Menu()
        SetupMeniu = wx.Menu()
        Help = wx.Menu()
        UndoBtn = EditMeniu.Append(wx.ID_UNDO, "&Undo\tCtrl+Z", "Undo action.")
        RedoBtn = EditMeniu.Append(wx.ID_REDO, "&Redo\tCtrl+Y", "Redo action.")
        EditMeniu.AppendSeparator()

        CutBtn = EditMeniu.Append(wx.ID_CUT, "&Cut\tCtrl+X", "Extract current selection.")
        CopyBtn = EditMeniu.Append(wx.ID_COPY, "&Copy\tCtrl+C", "Copy current selection.")
        PasteBtn = EditMeniu.Append(wx.ID_PASTE, "&Paste\tCtrl+V", "Paste selection from clipboard.")
        EditMeniu.AppendSeparator()

        FindAllBtn = EditMeniu.Append(wx.ID_FIND, "&Find all\tCtrl+F", "Find a certain text.")
        ReplaceBtn = EditMeniu.Append(wx.ID_REPLACE, "&Replace all\tCtrl+R", "Replace a certain text.")
        EditMeniu.AppendSeparator()

        SelectAllBtn = SelectMeniu.Append(wx.ID_SELECTALL, "&Select All\tCtrl+A", "Select the entire text in the document.")
        
        self.VLineNumber = ViewMeniu.Append(wx.ID_ANY, "&Line number", "Toggle the margin containing the line number on/off.", kind = wx.ITEM_CHECK)
        self.vVerticalScrollBar = ViewMeniu.Append(wx.ID_ANY, "&Vertical Scrollbar", "Toggle the vertical scrollbar on/off.", kind = wx.ITEM_CHECK) 
        self.VHorizontalScrollBar = ViewMeniu.Append(wx.ID_ANY, "&Horizontal Scrollbar", "Toggle the horizontal scrollbar (if shown) on/off.", kind = wx.ITEM_CHECK)
        ViewMeniu.AppendSeparator()        
        self.VStatusBar = ViewMeniu.Append(wx.ID_ANY, "&Statusbar", "Toggle the status bar on/off.", kind = wx.ITEM_CHECK)
        self.VToolBar = ViewMeniu.Append(wx.ID_ANY, "&Toolbar", "Toggle the tool bar on/off.", kind = wx.ITEM_CHECK)
        self.VProjectsBar = ViewMeniu.Append(wx.ID_ANY, "&Projects tab", "Toggle the projects tab on/off.", kind = wx.ITEM_CHECK)
        ViewMeniu.AppendSeparator()
        VConsole = ViewMeniu.Append(wx.ID_ANY, "&Close console\tESC", "Close the console.")
        self.LoadViewPrefs()
        NewMeniu = FileMeniu.Append(wx.ID_NEW, "&New\tCtrl+N", "Create a project file.")
        OpenMeniu = FileMeniu.Append(wx.ID_OPEN, "&Open\tCtrl+O", "Open an existing file.")
        SaveMeniu = FileMeniu.Append(wx.ID_SAVE, "&Save\tCtrl+S", "Save to your current file.")
        SaveAsMeniu = FileMeniu.Append(wx.ID_SAVEAS, "&Save as\tCtrl+Shift+S", "Save to a new file.")
        RunMeniu = CodeMeniu.Append(wx.ID_EXECUTE, "&Run\tF9", "Execute current code.")
        AddCmd = CodeMeniu.Append(wx.ID_ANY, "&Add command", "Add a command to the command line.")
        HAlkDocs = Help.Append(wx.ID_ANY, "&Alk Docs", "Search through alk documentation.")
        HAboutAlk = Help.Append(wx.ID_ANY, "&About Alk")
        HAboutIDE = Help.Append(wx.ID_ANY, "&About ALKA-47")
        AlkSetup = SetupMeniu.Append(wx.ID_ANY, "&Alk setup")

        BaraMeniu = wx.MenuBar() # bara de meniu de sus
        BaraMeniu.Append(FileMeniu, "&File")
        BaraMeniu.Append(EditMeniu, "&Edit")
        BaraMeniu.Append(SelectMeniu, "&Select")
        BaraMeniu.Append(ViewMeniu, "&View")
        BaraMeniu.Append(CodeMeniu, "&Code")
        BaraMeniu.Append(SettingsMeniu, "&Settings")
        SettingsMeniu.AppendSubMenu(SetupMeniu, "&Setup")
        BaraMeniu.Append(Help, "&Help")
        self.SetMenuBar(BaraMeniu)
        #evenimente butoane
        self.Bind(wx.EVT_MENU, self.RuleazaProgramul, RunMeniu)
        self.Bind(wx.EVT_MENU, self.FisierNou, NewMeniu)
        self.Bind(wx.EVT_MENU, self.DeschideFisier, OpenMeniu)
        self.Bind(wx.EVT_MENU, self.SalveazaFisier, SaveMeniu)
        self.Bind(wx.EVT_MENU, self.SalveazaFisierCa, SaveAsMeniu)
        self.Bind(wx.EVT_MENU, self.FaUndo, UndoBtn)
        self.Bind(wx.EVT_MENU, self.FaRedo, RedoBtn)
        self.Bind(wx.EVT_MENU, self.FaCut, CutBtn)
        self.Bind(wx.EVT_MENU, self.FaCopy, CopyBtn)
        self.Bind(wx.EVT_MENU, self.FaPaste, PasteBtn)
        self.Bind(wx.EVT_MENU, self.FaFind, FindAllBtn)
        self.Bind(wx.EVT_MENU, self.FaReplace, ReplaceBtn)
        self.Bind(wx.EVT_MENU, self.SelectAll, SelectAllBtn)
        self.Bind(wx.EVT_MENU, self.ToggleLineNumber, self.VLineNumber)
        self.Bind(wx.EVT_MENU, self.ToggleVScrollbar, self.vVerticalScrollBar)
        self.Bind(wx.EVT_MENU, self.ToggleHScrollbar, self.VHorizontalScrollBar)
        self.Bind(wx.EVT_MENU, self.ToggleStatusBar, self.VStatusBar)
        self.Bind(wx.EVT_MENU, self.ToggletoolsBar, self.VToolBar)
        self.Bind(wx.EVT_MENU, self.ToggleProjTab, self.VProjectsBar)
        self.Bind(wx.EVT_MENU, lambda event: self.InchideConsola(), VConsole)
        self.Bind(wx.EVT_MENU, self.OpenCmdMenu, AddCmd)
        self.Bind(wx.EVT_CLOSE, self.OnClose, self)
        self.Bind(wx.EVT_MENU, self.AboutIde, HAboutIDE)
        self.Bind(wx.EVT_MENU, self.AboutAlk, HAboutAlk)
        self.Bind(wx.EVT_MENU, self.AlkDocs, HAlkDocs)
        self.Bind(wx.EVT_MENU, self.OpenAlkSetupMenu, AlkSetup)
        if len(argv) > 0:
            self.DeschideProiect(argv)
        self.Show()
        if PREFERENCES.AlkSetup["SelectedAlkSetup"] == -1:
            setup = AlkSetupDialog(self)
            setup.ShowModal()
            setup.Destroy()
    def AboutIde(self, e):
        info = wx.adv.AboutDialogInfo()
        info.SetIcon(wx.Icon('bitmaps/IDE_icon.png', wx.BITMAP_TYPE_PNG))
        info.SetName("ALKA-47")
        info.SetVersion("v0.06")
        info.SetDescription("ALKA-47 is an IDE specially designed for the Alk programming language.\nFor now supports file management, multiple projects handler,\n syntax highlighting, auto identation and much more.")
        info.SetCopyright("(C) 2020 - 2021 Bodgan Inculeț")   
        info.SetWebSite("https://github.com/alk-language/Alk-IDE")
        wx.adv.AboutBox(info)
    def AlkDocs(self, e):
        info = wx.adv.AboutDialogInfo()
        info.SetName("Alk documentation")
        info.SetWebSite("https://github.com/alk-language/k-semantics/blob/master/doc/alk.pdf")
        wx.adv.AboutBox(info)
    def AboutAlk(self, e):
        about = """Alk is an algorithmic language intended to be used for teaching data structures and algorithms using an abstraction notation (independent of programming language). The goal is to have a language that: is simple to be easily understood;

        is expressive enough to describe a large class of algorithms from various problem domains;
        is abstract: the algorithm description must make abstraction of implementation details, e.g., the low-level representation of data;
        is a good mean for learning how to algorithmically think;
        supply a rigorous computation model suitable to analyse algorithms;
        is executable: the algorithm can be executed, even if they are partially designed;
        is accompanied by a set of tools helping to analyse the algorithm correctness and the eficiency;
        input and output are given as abstract data types, ignoring implementation details.
        There are two implementations of the Alk language:

        k-semantics (deprecated) - requires K3.6
        java-semantics (in progress)"""
        info = wx.adv.AboutDialogInfo()
        info.SetName("Alk programming language")
        info.SetVersion("v1.11")
        info.SetDescription(about)
        info.SetWebSite("https://github.com/alk-language")
        info.SetWebSite("https://github.com/alk-language/k-semantics/blob/master/doc/alk.pdf")
        wx.adv.AboutBox(info)
    def ToggleLineNumber(self, e):
        if self.VLineNumber.IsChecked():
            self.CodePart.SetMarginWidth(1, 40)
        else:
            self.CodePart.SetMarginWidth(1, 0)
        PREFERENCES.ViewSettings["LineNumber"] = self.VLineNumber.IsChecked()
        self.prefsModified = True
    def ToggleVScrollbar(self, e):
        self.CodePart.SetUseVerticalScrollBar(self.vVerticalScrollBar.IsChecked())
        PREFERENCES.ViewSettings["VerticalScrollBar"] = self.vVerticalScrollBar.IsChecked()
        self.prefsModified = True
    def ToggleHScrollbar(self, e):
        self.CodePart.SetUseHorizontalScrollBar(self.VHorizontalScrollBar.IsChecked())
        PREFERENCES.ViewSettings["HorizontalScrollBar"] = self.VHorizontalScrollBar.IsChecked()
        self.prefsModified = True
    def ToggleStatusBar(self, e):
        if self.VStatusBar.IsChecked():
            self.StatusBar.Show()
        else:
            self.StatusBar.Hide()
        PREFERENCES.ViewSettings["StatusBar"] = self.VStatusBar.IsChecked()
        self.prefsModified = True
        self.SetSize(wx.Size(self.Size[0] - 1, self.Size[1]))
        self.SetSize(wx.Size(self.Size[0] + 1, self.Size[1]))
    def OnClose(self, event):
        tabs = self.panel.textTabs
        if event.CanVeto() and self.prefsModified:
            if wx.MessageBox("Do you want to save the current layout of the editor?", "Please confirm", wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
                PREFERENCES.SaveViewSettingPrefs()
                if not tabs.AreSavedAll():
                    if wx.MessageBox("Do you want to save your current project(s)?", "Save progress", wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
                        unsaved = tabs.SaveAll()
                        if unsaved > 0:
                            if wx.MessageBox("You have " + str(unsaved) + " file(s) with no current directory path, please make sure you save them manually.", "Save manually", wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
                                return   
                            else:
                                event.Veto()
                                self.Destroy()
                        else:
                            self.Destroy()
                    else:
                        self.Destroy()                   
            else:
                if not tabs.AreSavedAll():
                    if wx.MessageBox("Do you want to save your current project(s)?", "Save progress", wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
                        unsaved = tabs.SaveAll()
                        if unsaved > 0:
                            if wx.MessageBox("You have " + str(unsaved) + " file(s) with no current directory path, please make sure you save them manually.", "Save manually", wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
                                return   
                            else:
                                event.Veto()
                                self.Destroy()
                        else:
                            self.Destroy()
                    else:
                        self.Destroy()
        elif event.CanVeto() and not tabs.AreSavedAll():
            if wx.MessageBox("Do you want to save your current project(s)?", "Save progress", wx.ICON_QUESTION | wx.YES_NO) == wx.YES:
                unsaved = tabs.SaveAll()
                if unsaved > 0:
                    if wx.MessageBox("You have " + str(unsaved) + " file(s) with no current directory path, please make sure you save them manually.", "Save manually", wx.ICON_QUESTION|wx.YES_NO) == wx.YES:
                        return   
                    else:
                        event.Veto()
                        self.Destroy()
                else:
                    self.Destroy()
            else:
                self.Destroy() 
        self.Destroy()
    def ToggleProjTab(self, e):
        if self.VProjectsBar.IsChecked():
            self.panel.textTabs.Show()
        else:
            self.panel.textTabs.Hide()
        PREFERENCES.ViewSettings["ProjectsTab"] = self.VProjectsBar.IsChecked()
        self.prefsModified = True
        self.panel.Layout()
    def ToggletoolsBar(self, e):
        if self.VToolBar.IsChecked():
            self.toolBar.Show()
        else:
            self.toolBar.Hide()
        PREFERENCES.ViewSettings["Toolbar"] = self.VToolBar.IsChecked()
        self.prefsModified = True
        self.SetSize(wx.Size(self.Size[0] - 1, self.Size[1]))
        self.SetSize(wx.Size(self.Size[0] + 1, self.Size[1]))
    def OpenAlkSetupMenu(self, e):
        setup = AlkSetupDialog(self)
        setup.ShowModal()
        setup.Destroy()
    def OpenCmdMenu(self, e):
        cmd = CmdDialog(self)
        cmd.ShowModal()
        cmd.Destroy()
    def LoadViewPrefs(self):
        prefs = PREFERENCES.ViewSettings
        if prefs["LineNumber"]:
            self.VLineNumber.Check()
        else:
            self.CodePart.SetMarginWidth(1, 0)
        if prefs["VerticalScrollBar"]:
            self.vVerticalScrollBar.Check()
        else:
            self.CodePart.SetUseVerticalScrollBar(False)
        if prefs["HorizontalScrollBar"]:
            self.VHorizontalScrollBar.Check()
        else:
            self.CodePart.SetUseHorizontalScrollBar(False)
        if prefs["StatusBar"]:
            self.VStatusBar.Check()
        else:
            self.StatusBar.Hide()
        if prefs["Toolbar"]:
            self.VToolBar.Check()
        else:
            self.toolBar.Hide()
        if prefs["ProjectsTab"]:
            self.VProjectsBar.Check()
        else:
            self.panel.textTabs.Hide()
    def FaUndo(self, e):
        self.CodePart.Undo()
    def FaRedo(self, e):
        self.CodePart.Redo()
    def FaCut(self, e):
        self.CodePart.Cut()
    def FaCopy(self, e):
        self.CodePart.Copy()
    def FaPaste(self, e):
        self.CodePart.Paste()
    def FaFind(self, e):
        c = FindDialog(self, self.CodePart)
        c.ShowModal()
        c.Destroy()
    def FaReplace(self, e):
        c = ReplaceDialog(self, self.CodePart)
        c.ShowModal()
        c.Destroy()
    def SelectAll(self, e):
        self.CodePart.SelectAll()
    def RuleazaProgramul(self, e):
        if len(self.panel.textTabs.tabs) == 0:
            return
        if PREFERENCES.AlkSetup["SelectedAlkSetup"] > -1: #daca am vreun fisier alk localizat
            self.DeschideConsola(False)
            if self.panel.consola.ApasatPeInput is True:
                self.panel.consola.ApasatPeInput = False
                global INPUT
                CommandInput = ""
                CommandInput += INPUT
                ComandaInput = CommandInput.replace('\n', '')
                ComandaInput = ComandaInput.replace(" ", "")
                if len(CommandInput) > 0:
                    global INPUT_INDEX
                    global INPUT_CMD
                    c = "-i " + '"' + ComandaInput + '"'
                    if not INPUT_CMD is None:
                        GLOBAL_CMDS.remove(INPUT_CMD)
                        INPUT_CMD = None
                    GLOBAL_CMDS.append(c)
                    INPUT_INDEX = len(GLOBAL_CMDS) - 1
                    INPUT_CMD = GLOBAL_CMDS[INPUT_INDEX] # ultimul elem
                else:
                    if not INPUT_CMD is None:
                        GLOBAL_CMDS.remove(INPUT_CMD)
                        INPUT_CMD = None
            self.panel.consola.TextConsola.SetValue("")
            self.panel.consola.TextConsola.AppendText("Using jarfile with path: " + PREFERENCES.AlkSetup["AlkJarPathFiles"][PREFERENCES.AlkSetup["SelectedAlkSetup"]] + '\n')
        else:
            setup = AlkSetupDialog(self)
            setup.ShowModal()
            setup.Destroy()
            #self.panel.consola.Eroare("JAR file could NOT be located" + ". Make sure that alk.jar is downloaded and available at " + self.numeDirector +"\\bin\\alk\\" + '\n')
            return            
        if len(self.panel.text.CurentTab.FilePath) == 0:
            CaleProiect = os.path.join(self.tmpDir, "_tmp.alk") #daca nu am salvat, salvez intr-un fisier temporar
        else:
            CaleProiect = os.path.join(self.panel.text.CurentTab.FilePath, self.panel.text.CurentTab.FileName)
            self.panel.text.CurentTab.MarkAsSaved()
        f = open(CaleProiect, "w")
        f.write(self.CodePart.GetValue())
        f.close()
        cmd = "java -jar " + PREFERENCES.AlkSetup["AlkJarPathFiles"][PREFERENCES.AlkSetup["SelectedAlkSetup"]] + " -a " + CaleProiect
        if len(GLOBAL_CMDS) > 0:
            for i in GLOBAL_CMDS:
                cmd += ' ' + i
        p = Popen(cmd, stdout = PIPE , stderr = PIPE, universal_newlines = True, shell = True)

        for line in iter(p.stdout.readline,''):
            line = line.rstrip()
            self.panel.consola.TextConsola.AppendText(line + '\n')
            #if self.panel.consola.TextConsola.GetNumberOfLines() == 300: # golesc consola
                #self.panel.consola.TextConsola.SetValue("")
        pos = self.panel.consola.TextConsola.GetInsertionPoint() # sterg ultima linie ca mi da un endline in plus
        self.panel.consola.TextConsola.Remove(pos - 1 , pos)
        errors = p.communicate()[1]
        returnCode = p.returncode
        if len(errors) > 0 :   # adica daca am vreo eroare
            linie = errors.find("line")
            if linie > -1:
                linieEroare = list(map(int, re.findall(r'\d+', errors)))  # iau numarul liniei la care se afla eroarea
                self.markereErori.append(self.CodePart.MarkerAdd(linieEroare[0] - 1,1)) #pun un marker pe linia aia
            self.panel.consola.Eroare(errors + '\n')
        else:
            #sir = self.LiniiCod.GetValue()
            #i = self.LiniiCod.GetCurrentPos()
            #print(sir[i])
            if len(self.markereErori) > 0:
                for i in self.markereErori:
                    self.CodePart.MarkerDeleteHandle(i)
                self.markereErori.clear()
            self.StatusBar.SetStatusText("", 0)
        self.panel.consola.TextConsola.AppendText('\n' + "Execution ended with return code " + str(returnCode) + ".\n")
     
    def DeschideConsola(self, e):
        self.panel.consola.Show()
        self.panel.Layout()
        if e is True:
            self.panel.consola.Input(e)
        else:
            self.panel.consola.TextConsola.SetEditable(False)
    def InchideConsola(self):
        self.panel.consola.Hide()
        self.panel.consola.TextConsola.SetEditable(False)
        self.panel.Layout()
    def DeschideFisier(self, e):
        try:
            casuta = wx.FileDialog(self, "Choose a file", self.numeDirector, "", "*.alk*", wx.FD_OPEN)
            if casuta.ShowModal() == wx.ID_OK:
                self.panel.textTabs.AddTab(casuta.GetDirectory(), casuta.GetFilename(), False)
            casuta.Destroy()
        except:
            casuta = wx.MessageDialog(self, "Couldn't open the specified file.", "Error", wx.ICON_ERROR)
            casuta.ShowModal()
            casuta.Destroy()
    def DeschideProiect(self, cale):
        #pentru ceva viitor multitab opener in care nu pot avea mai multe  instante ale aceluiasi program
        """
        for proc in psutil.process_iter():
            try:
                processName = proc.name()
                processID = proc.pid
                if processName == "ALKA-47.exe" and processID != os.getpid():
                    self.Destroy()
                    return
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
            """
        if len(cale) == 1:
            if os.path.isfile(str(cale[0])):
                dirname ,appname = os.path.split(str(cale[0]))
                if appname != "ALKA-47.exe" and appname != "ALKA-47.py":
                    f = open(str(cale[0]))
                    strin = f.read()
                    f.close()
                    self.CodePart.SetValue(strin)
                    self.panel.text.CurentTab.SetFilePath(dirname)
                    self.panel.text.CurentTab.SetFileName(appname)
                    self.panel.text.CurentTab.MarkAsSaved()
        else:
            if os.path.isfile(str(cale[1])):
                f = open(str(cale[1]))
                strin = f.read()
                f.close()
                dirname ,appname = os.path.split(str(cale[1]))
                self.CodePart.SetValue(strin)
                self.panel.text.CurentTab.SetFilePath(dirname)
                self.panel.text.CurentTab.SetFileName(appname)
                self.panel.text.CurentTab.MarkAsSaved()
    def SalveazaFisier(self, e):
        tab = self.panel.text.CurentTab
        if tab.Saved or len(tab.FilePath) > 0:
            f = open(os.path.join(tab.FilePath, tab.FileName), 'w')
            f.write(self.CodePart.GetValue())
            tab.MarkAsSaved()
            f.close()
        else:
            casuta = wx.FileDialog(self, "Save file as...", tab.FileName, "Untitled", ".alk", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if casuta.ShowModal() == wx.ID_OK:
                f = open(os.path.join(casuta.GetDirectory(), casuta.GetFilename()), 'w')
                f.write(self.CodePart.GetValue())
                f.close()
                tab.TmpCnt = "" #sterg stringul temporar pt ca nu mai am nevoie de el
                tab.SetFileName(casuta.GetFilename())
                tab.SetFilePath(casuta.GetDirectory())
                tab.MarkAsSaved()
            casuta.Destroy()
    
    def SalveazaFisierCa(self, e):
        try:
            tab = self.panel.text.CurentTab
            casuta = wx.FileDialog(self, "Save file as...", self.numeDirector, "Untitled", ".alk", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            if casuta.ShowModal() == wx.ID_OK:
                f = open(os.path.join(casuta.GetDirectory(), casuta.GetFilename()), 'w')
                f.write(self.CodePart.GetValue())
                f.close()
                tab.TmpCnt = ""
                tab.SetFileName(casuta.GetFilename())
                tab.SetFilePath(casuta.GetDirectory())
                tab.Saved = True
            casuta.Destroy()
        except:
            pass

    def FisierNou(self, e):
        self.panel.textTabs.AddTab("", "", True)
        self.CodePart.SetValue("")
        

def main(argv):
    global WIN
    WIN = os.name == "nt"
    opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    aplicatie = wx.App()
    fereastra = FereastraPrincipala(None, "ALKA-47 v0.06", args)
    aplicatie.MainLoop()
if __name__ == "__main__":
    main(sys.argv)