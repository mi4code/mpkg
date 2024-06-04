import sys, traceback, platform, os, shlex



###  utils  ###

# RULE: directory path should not end with / ($HOME/Packages)

def _normalize_name(name):
    name = name.lower()
    # first is always prefered
    words = [
        ["", "any", "all"],
    
        ["windows", "win", "wine", "hangover"],
        ["linux"],
        
        ["x86_64", "x64", "amd64"],
        ["x86_32", "x32", "x86", "i386", "i686"],
        ["aarch64","arm64"],
        ["aarch32", "arm32", "armhf", "armv7", "armv6l"],
        
        ["binary", "exe", "bin"],
        #["shell", "bat", "sh", "cmd"], # should be split by os; https://stackoverflow.com/questions/5079180/what-is-the-difference-between-batch-and-bash-files
        ["script-batch", "bat"],
        ["script-bash", "script-sh", "bash", "sh"], # TODO: bash and sh are two different things: https://stackoverflow.com/questions/5725296/difference-between-sh-and-bash
        ["python", "py", "python3"],

        ]
        
    for w in words:
        if name in w: return w[0]
        
    return name

def _is_compatible(a,b):
    if type(a) == type([]) and type(b) == type([]): return _is_compatible(a[0],b[0]) and _is_compatible(a[1],b[1]) and _is_compatible(a[2],b[2])
    a = _normalize_name(a)
    b = _normalize_name(b)
    if a == b: return True
    if a == "" or b == "": return True # normalized name for "any" is ""
    return False

def _load_format_py(file):
    vars = {}
    exec( open(file).read(), vars, vars)
    vars.pop("__builtins__")
    return vars

def _filedetect(file_path):
    suffix = file_path.split('.')[-1].lower() if '.' in file_path.split('/')[-1] else None
    
    def detect():

        os = ""
        type = ""
        architecture = ""

        if suffix in ["exe","dll","com"]:
        
            os = "win"
        
            if suffix in ["exe","com"]: type = "bin"
            elif suffix in ["dll"]: type = "lib"
            
        
            with open(file_path, 'rb') as f:
            
                # Read the first 2 bytes to check for the PE signature
                if f.read(2) != b'MZ':  return "exedetect-error-MZ"

                # Seek to the offset of the PE signature (at 0x3C)
                f.seek(0x3C)
                pe_offset = int.from_bytes(f.read(4), 'little')

                # Seek to the PE signature
                f.seek(pe_offset)
                if f.read(4) != b'PE\0\0':  return "exedetect-error-PE"

                # Seek to the offset of the machine architecture - not needed (we got there with previous read)
                #f.seek(pe_offset+4) 
                
                machine = int.from_bytes(f.read(2), 'little')

                architecture = {
                    0x14c: "x32",
                    0x8664: "x64",
                    0xaa64: "arm64",
                    0x1c0: "arm32",
                    0x1c4: "arm32"
                }.get(machine, "exedetect-error-"+str(hex(machine)))
                
                if architecture.startswith("bindetect-error-"): return architecture

        elif suffix in ["bat"]:
            os = "win"
            type = "script-batch"
            
        elif suffix in [None,"sh"] and open(file_path, 'r').readline()[0:len("#!/")] == "#!/":
            line = open(file_path, 'r').readline()
            #os = "linux"
            type = "script-"+open(file_path, 'r').readline().split("/")[-1].split(" ")[-1]

        elif suffix in [None,"so","appimage"]:
        
            os = "linux" # only linux for now
        
            if suffix in [None,"appimage"]: type = "bin"
            elif suffix in ["so"]: type = "lib"


            with open(file_path, 'rb') as f:
            
                # Read the first 4 bytes to check for the ELF magic number
                if f.read(4) != b'\x7fELF':  return "bindetect-error-ELF"
                
                f.seek(0x05)
                endianness = "little" if f.read(1)[0] == 1 else "big"  # when its 2  ## list converts bytes to numbers

                # Seek to the offset of the architecture and target system
                #f.seek(0x07)
                #if f.read(1).hex() != 0x03: return "bindetect-error-notlinux"  ## ignore it because some file dont have set proper value
                
                f.seek(0x12)
                machine = int.from_bytes(f.read(2), endianness)
                
                architecture = {
                    0x03: "x32",
                    0x3E: "x64",
                    0xB7: "arm64",
                    0x28: "arm32"
                }.get(machine, "bindetect-error-"+str(hex(machine)))
                
                if architecture.startswith("bindetect-error-"): return architecture
       
        
        return [os,type,architecture]
    
    d = detect()
    return d if type(d)==type([]) else ["unknown","unknown","unknown"]


_thisfile = __file__.replace("\\","/")  # or sys.argv[0]


###  runners  ###

_system = [_normalize_name(platform.system()), "", _normalize_name(platform.machine())] # os, type, architecture
_runners = [] # should be filtered for current system? - nope this does the cmd gen

## TODO: multiple runs_on & runs_what

class Runner ():
    name = ""
    runs_on = ["","",""]
    runs_what = ["","",""]
    command = lambda x: None
    # availible = Lambda bool - is the runner installed? is enabled?
    def __init__(self,n,o,w,c):
        self.name = n
        self.runs_on = o
        self.runs_what = w
        self.command = c
        
        _runners.append(self)

# windows
Runner(
    "windows-native",
    ["win","",_system[2]],
    ["win","exe",_system[2]],
    lambda x:  'start "" /B ' + x
    )
'''
No setup (except installing Windows) required.
'''

Runner(
    "windows-batch",
    ["win","",""],
    ["win","script-batch",""],
    lambda x:  'start "" /B ' + x
    )
'''
No setup (except installing Windows) required.
'''
    
Runner(
    "windows-wow64",
    ["win","","x64"],
    ["win","exe","x32"],
    lambda x:  'start "" /B ' + x
    )
Runner(
    "windows-wow64arm",
    ["win","","arm64"],
    ["win","exe","arm32"],
    lambda x:  'start "" /B ' + x
    )
'''
No setup (except installing Windows) required.
Works only on 64-bit systems. (Not sure about Windows on ARM: https://stackoverflow.com/questions/72023405/application-compatibility-on-arm-for-windows)
'''

Runner(
    "windows-win32onarm",
    ["win","","arm64"],
    ["win","exe","x32"],
    lambda x:  'start "" /B ' + x
    )
Runner(
    "windows-win64onarm",
    ["win","","arm64"],
    ["win","exe","x64"],
    lambda x:  'start "" /B ' + x
    )
'''
No setup (except installing Windows) required.
Depends on windows version - see https://stackoverflow.com/questions/72023405/application-compatibility-on-arm-for-windows
'''

# linux
Runner(
    "linux-native",
    ["linux","",_system[2]],
    ["linux","bin",_system[2]],
    lambda x: x
    )
'''
No setup required.
'''
Runner(
    "linux-bash",
    ["linux","",""],
    ["linux","script-bash",""],
    lambda x: x
    )
'''
No setup required.
'''
Runner(
    "linux-winehq",
    ["linux","",""],
    ["win","bin",_system[2]],
    lambda x: "wine "+x
    )
'''
TODO: wineHQ
'''


###  library + cli  ###

MPKG_DATAPROFILE = _thisfile[0:_thisfile.index("/mpkg/variants")]+"/mpkg/data/default"
def generate_path(system=_system, portable=False): ## TODO: add portable mode calling mpkg run
    
    for p in os.listdir(  MPKG_REPO_VARIANTDIR[0:MPKG_REPO_VARIANTDIR.index("/<package>")]  ):
        p = Package(p)
        for b in p.PREFERENCES["add_to_path"].split(",") if "add_to_path" in p.PREFERENCES.keys() else []:
        
            if _is_compatible(system[0],"windows"):
                open( MPKG_DATAPROFILE+"/path/"+b+".bat" , 'w').write( p.command(command=b,args="%*",system=system) )
            
            elif _is_compatible(system[0],"linux"):
                open( MPKG_DATAPROFILE+"/path/"+b , 'w').write( "#!/bin/bash\n"+p.command(command=b,args="$@",system=system) )

def generate_apps(system=_system, portable=False): ## TODO: handle icons and fancy name

    def create_lnk (file, name, command):

        import os, winshell
        from win32com.client import Dispatch

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(file)  # *.lnk
        shortcut.Targetpath = MPKG_DATAPROFILE+"/apps/"+name+".bat" # uses helper script
        #shortcut.Targetpath = shlex.split(command)[0]
        #shortcut.Arguments = command[0:command.index(" ", len( shlex.split(command)[0] ))]
        shortcut.WorkingDirectory = "%USERPROFILE%" # $HOME %USERPROFILE%
        shortcut.IconLocation = shlex.split(command.replace('start "" /B ',''))[0]
        #shortcut.IconLocation = shortcut.Targetpath
        shortcut.save()
        
 
    def create_desktop (file, name, command):
        
        desktop = open(file,'w')  # *.desktop
        content = """[Desktop Entry]
        Type=Application
        Version=1.0

        Name="""+name+"""
        #Comment=
        #Categories=

        Exec="""+command+"""
        Path=$HOME
        #Terminal=false/true
        #Icon=image
        """

        desktop.write(content)
        desktop.close()
        

    for p in os.listdir(  MPKG_REPO_VARIANTDIR[0:MPKG_REPO_VARIANTDIR.index("/<package>")]  ):
        p = Package(p)
        for b in p.PREFERENCES["add_to_apps"].split(",") if "add_to_apps" in p.PREFERENCES.keys() else []:
        
            if _is_compatible(system[0],"windows"):
                open( MPKG_DATAPROFILE+"/apps/"+b+".bat" , 'w').write( p.command(command=b,args="%*",system=system) ) # helper
                create_lnk ( MPKG_DATAPROFILE+"/apps/"+b+".lnk", b, p.command(command=b,args="%*",system=system) )
            
            elif _is_compatible(system[0],"linux"):
                create_desktop ( MPKG_DATAPROFILE+"/apps/"+b+".desktop", b, p.command(command=b,args="$@",system=system) )


# expecting that directories contain only expected content 
# variables: <package>, <data>, <variant>
MPKG_REPO_DATADIR = _thisfile[0:_thisfile.index("/mpkg/variants")]+"/<package>/data/<data>"
MPKG_REPO_VARIANTDIR = _thisfile[0:_thisfile.index("/mpkg/variants")]+"/<package>/variants/<variant>"
MPKG_REPO_PACKAGEFILE = _thisfile[0:_thisfile.index("/mpkg/variants")]+"/<package>/<package>.mpkg"

## TODO: return back predefined os,type,arch

class Package:
    def __init__(self, name):
    
        ### know the package name thus dirs ###
        ## TODO: check whether file path matches the repo (then treat it as from repo)
        if "/" in name or "\\" in name: # packagefile
            name = name.replace("\\","/")
            self.NAME = name.split("/")[-2]
            self.DATADIR = name[0:-len("/"+self.NAME+".mpkg")]+"/data/<data>"
            self.VARIANTDIR = name[0:-len("/"+self.NAME+".mpkg")]+"/variants/<variant>"
            self.PACKAGEFILE = name
            print(self.NAME, name)
        
        else: # package from repo
            self.NAME = name
            self.DATADIR = MPKG_REPO_DATADIR.replace("<package>", self.NAME)
            self.VARIANTDIR = MPKG_REPO_VARIANTDIR.replace("<package>", self.NAME)
            self.PACKAGEFILE = MPKG_REPO_PACKAGEFILE.replace("<package>", self.NAME)
    
        ### load preferences ###
        # load package preferences from *.mpkg file into dict{str:str}
        self.PREFERENCES = _load_format_py( self.PACKAGEFILE )
        
        ### load variants ###
        # ~not needed

        ### load data ###
        # ~not needed
        
        pass
        
    def get_dataprofiles(self, unprocessed=False): # gives data profiles names, if default exists it puts it to the first place
        return sorted(os.listdir(self.DATADIR[0:self.DATADIR.index("/<data>")]), key = lambda x: int(x=="default") )
        
    def get_variants(self, unprocessed=False): # gives variant names, that are not disabled, sorts them according to prefered_variants 
        return sorted(
            filter(
                (lambda x: not (x in self.PREFERENCES["disabled_variants"].split(",")))   if "disabled_variants" in self.PREFERENCES else   (lambda x: True),
                os.listdir(self.VARIANTDIR[0:self.VARIANTDIR.index("/<variant>")]), 
                ),
            key = (lambda x: self.PREFERENCES["prefered_variants"].split(",").index(x) if x in self.PREFERENCES["prefered_variants"].split(",") else len(self.PREFERENCES["prefered_variants"].split(",")))   if "prefered_variants" in self.PREFERENCES else   (lambda x: 0) 
            )
        
    def command(self, command=None, args=[], data=None, variant=None, system=None):
        if command == None: command = self.PREFERENCES["run_default"]
        if system == None: system = _system
        if data == None: data = self.get_dataprofiles()[0]
        if variant == None: # find variant not a binary
            
            # filter disabled and sort variants so prefered will be checked for compatibility first
            # every variant can contain multiple binaries/files for multiple systems but we silently expect that these subvariants are equal (so we can use any binary to do the compatibility eval magic) -> so we can usse run_default to detect supported systems

            def _ ():
                for r in _runners:
                    if _is_compatible(r.runs_on, system):
                    
                        for v in self.get_variants():
                            for c in  _load_format_py(self.VARIANTDIR.replace("<variant>", v)+"/MPKG")["content"]:
                                if c["name"] == command and _is_compatible(r.runs_what, _filedetect(c["file"].replace("$MPKG_PACKAGE",self.VARIANTDIR.replace("<variant>", v)).replace("%MPKG_PACKAGE%",self.VARIANTDIR.replace("<variant>", v)))  ):
                                    #variant = v
                                    return v #break
            variant = _()
            
            # we expect that there is one version for every possible hardware configuration; we sort them from latest/prefered, then we go trough runners from the most native
            # lets not confuse "variant" (downloadable - should be same version; can be preferd/disabled), "binary" (subset of content), "content" (all interresting files in variant)
            # what if there is oldish native and latest almost native?  - this will ron the oldish - should it? - yeah, otherwise you should have disabled the oldish
            # what if i want prefer only part of variant (ie x32 from one and x64 from other package ~ both x32+x64)? you are out of luck
    
    
        # these shouldnt be permanently changed to selected one
        #self.DATADIR = self.DATADIR.replace("<data>", data)
        #self.VARIANTDIR = self.VARIANTDIR.replace("<variant>", variant)
        
        cmd = 'echo "mpkg couldnt find compatible variant"' ## TODO: add better cant run handler
        
        for r in _runners:
            if _is_compatible(r.runs_on, system):
                for c in  _load_format_py(self.VARIANTDIR.replace("<variant>", variant)+"/MPKG")["content"]:
                    if c["name"] == command and _is_compatible(r.runs_what, _filedetect(c["file"].replace("$MPKG_PACKAGE",self.VARIANTDIR.replace("<variant>", variant)).replace("%MPKG_PACKAGE%",self.VARIANTDIR.replace("<variant>", variant)))  ):
                        cmd = r.command(
                            '"'+c["file"].replace("$MPKG_PACKAGE",self.VARIANTDIR.replace("<variant>", variant)).replace("%MPKG_PACKAGE%",self.VARIANTDIR.replace("<variant>", variant))
                            +'" '+c["args"]
                            .replace("$MPKG_DATA",self.DATADIR.replace("<data>", data))
                            .replace("%MPKG_DATA%",self.DATADIR.replace("<data>", data))
                            .replace("$MPKG_ARGS", args if type(args)==type("") else " ".join(['"'+a+'"' if " " in a else a for a in args]) )
                            .replace("%MPKG_ARGS%", args if type(args)==type("") else " ".join(['"'+a+'"' if " " in a else a for a in args]) )
                            
                        )
                        
        return cmd

    def run (self, *args, **kwargs):
        cmd = self.command(*args, **kwargs)

        try:
            subprocess.call(shlex.split(cmd)) # some doesnt work with os.system
        except:
            os.system(cmd) # for admin


### main ###
    
if __name__ == "__main__":

    if len(sys.argv) >= 2:
        if sys.argv[1] == "run":
            Package(sys.argv[2]).run(args=sys.argv[3:])
        else:
            Package(sys.argv[1]).run(args=sys.argv[2:])
            
        
    else:
        print("---   mpkg python cmdline   ---")
        exit = False
        while not exit: 
            try:
                c = input(">> ")
                if c == "exit": exit = True
                else: print(""+str(eval(c)))
            except:
                print(" ",traceback.format_exc().replace("\n","\n "))
