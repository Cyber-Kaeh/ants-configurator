## ants-configurator
```
_________   _____  ___      ___ ________  ________     
|\___   ___\/ __  \|\  \    /  /|\   __  \|\   ____\    
\|___ \  \_|\/_|\  \ \  \  /  / | \  \|\  \ \  \___|    
     \ \  \\|/ \ \  \ \  \/  / / \ \  \\\  \ \  \       
      \ \  \    \ \  \ \    / /   \ \  \\\  \ \  \____  
       \ \__\    \ \__\ \__/ /     \ \_____  \ \_______\
        \|__|     \|__|\|__|/       \|___| \__\|_______|
                                          \|__|         
```

A menu driven CLI tool to help speed up the post-imaging process for ThinkHub devices.

## Quick Start

Clone this repository to the target device.  
`git clone github.com/Cyber-Kaeh/ants-configurator.git`

Navigate inside the dir.  
`cd ants-configurator`

Run the  pex app.  
`python ants-configurator.pex`

Or run source.  
`python -m src`

Go through the menus to commence configuratortating! Or jump around as needed. 
The information you enter into the app, such as screen count, screen resolutioin, dock names, etc.,
is saved automatically in the app then reloaded if you quit and re-open configurator.
Defaults and commands are sent in real time and you will get feedback on their success/failure.  
  
Configuration file is located at:  
`~/.config/ants-configurator/app_state.json`


## Packaging with Pex

```Bash
pex . -o ants-configurator.pex -c ants-configurator --sh-boot
```
