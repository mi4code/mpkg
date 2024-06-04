# mpkg

mpkg is package manager / application management tool providing option for having portable applications that will run on (almost) any software and hardware configuration

moreover these packages / apps are human-managable - you can install/uninstall/update them only using file manager and text editor (or just terminal)


## current status

**(CURRENTLY THIS PROJECT IS IN EARLY DEVELOPEMENT STAGE AND THE FUNCTIONALITY IS QUITE LIMITED)**

mpkg can run either:\
 self-contained linux applications:  AppDir / AppImage (extracted to be AppDir ~optional) / any user-made (expected to be self-contained or be run systems having required dependencies)\
 portable windows applications:  any portable application (being it directory or single exe)\
 scripts

the packages can be managed "by hand" - by simply adding/removing directories with binaries

<!--
## approach

Today the self-contained strategy doesnt represent a big problem - since we have enough storage space and file deduplication; anyway, the modern packaging methods (flatpak, snap) do the same thing

-->


## file format

### `MPKG` file
present in every version directory, describes all files there

(currently only python format is availible)

**example:**

```
version = '1'
```
*the version of the package*
```
compatible_100 = '1'
```
*(optional) identifies if the package is 100% compatible with the mpkg concept of "is portable, doesnt leave any files outside its directory"*
*requirements:*
 - the version package never changes its contents
 - if the app stores any configs it should be able to relocate them to the right directory (and those should be cross-platform and ideally cross-version)
 - when storing temporary files, it should use the system default directory
```
content = [{
	'name' : 'runme',
	'file' : '$MPKG_PACKAGE/runme',
	'args' : '$MPKG_ARGS --use-config "$MPKG_DATA"',
	'type' : 'binary',
	'os' : 'linux',
	'architecture' : 'AMD64'
	},
	...]
```
*list of dicts describing all the interesting files*
*keys:*
 - `file` - file this entry is refering to ~~(in case of binaries, there may/should be also the config parameters for portable mode, then everything should be properly quotated with `"`), you will have to use following variables: `$MPKG_DATA`, `$MPKG_PACKAGE`, `$MPKG_ARGS` (or `%MPKG_PACKAGE%` and so)~~
 - `args` - when file is binary, command line options that relocate the configs,  you should use following variables: `$MPKG_DATA`, `$MPKG_PACKAGE`, `$MPKG_ARGS` (or `%MPKG_PACKAGE%` and so)
 - `name` - ie. command or library invocation name
 - `type` - type of the file (possible values: `binary`, `script-<one of supported types>`, `library`, `source`, `headers/include`)
 - `os` - name of operating system this file is for natively (or blank)
 - `architecture` - compatible processor architecture
\
note: `type`,`os` and `architecture` are optional - can be auto-detected for [ELF binaries (includes AppImages)](https://superuser.com/questions/791506/how-to-determine-if-a-linux-binary-file-is-32-bit-or-64-bit), [PE executables](https://superuser.com/questions/358434/how-to-check-if-a-binary-is-32-or-64-bit-on-windows) and scripts with shebang (except those that use some binaries - in fact all use, but those in the package represent the problem)


### `*.mpkg` file
is the package settings file (sets all the what, when and how to run)\
(the format is not completed yet; only python format again)
**example:**
```
run_default = 'runme'
```
*says what to run when the file = the package is run by default*
```
prefered_variants = 'runme-win64-v0.1.0,runme-linux64-v2.3.0'
```
*version selection (comma-separated list of variant that are prefered - you can run older version/differen version on linux an windows)*
```
disabled_variants = 'runme-win64-v0.1.0,runme-linux64-v2.3.0'
```
*version selection (comma-separated list of variant that are disabled - you can run force running nonnative versions - this time likely win32)*
```
add_to_path = 'runme'
```
*adds binary to path*
```
add_to_apps = 'runme'
```
*creates shortcut to the binary for app menu/etc*
```
notes = 'this is an example\n😀'
```
*user notes*
 
 
### directory structure
`/<package name>/data/*` - directories for user data\
`/<package name>/package/*` - directories containing binaries, libs, header files, etc (should be read-only)\
`/<package name>/src` - currently place for any file used when handcrafting the package, in the future it may be used for self-building packages \
`/<package name>/*.mpkg` - mpkg file, se above\


## todos
 - OVERRIDE CONFIG PARAMETERS
 - ERROR/MISSING HANDLING
 - APP SUPPORT WITH FANCY NAME AND ICON
 - RESEARCH python pip venv AND OTHER LANGUAGES (LIKE java)
 - OS VERSION SUPPORT
 - SELF BUILDABLE PACKAGES
 - DEPENDENCY SUPPORT
 - SANDBOXING/PERMISSIONS
 - ADD DOCKER/OCI
 - RESEARCH FatELF
 - APP DB / mpkg install (native)
 - common/per-version portable commands + portable workarounds
 - variant-builder (MPKG)
 - mpkg install-appimage/install-appdir
 - return back override of file autodetect (os,type,architecture in MPKG)