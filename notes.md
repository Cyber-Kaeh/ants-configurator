## 3/3 First run after pex

### Bugs
- Save state isn't working as expected. Its also putting an app_state.json outside the app, and stays empty.

- I'm noticing a hang after the output box dissapears. Have to hit Esc to return menu control access. Also happened after alt+tabing back into app.
    - Reproduced by going to software vc > enable both > tab into output box and copy text. If you hit 'h' without exiting the output box first (with either tab or Esc) then it gets stuck and you have to Esc. Maybe a better UI signal to let user know what is happening if a programmatic fix can't be found.

- Inconsistent results from setting defaults write com.t1visions.automate VCCaptureRect. I think its a saving issue because I exited the app and ran defaults again, getting different results.

### Features
- Add a back button to all the menus so user can click back. Or find a way to put a callback on the b - back on the bottom toolbar. Maybe both!

- Progress bars! Unclear to the user when a command is running or not. Especially longer running commands like find integral id.


### Displays Menu
No feedback on touchDisplayResolution.
Added to_panel decorator, may need more tweaking. line 152

All defaults write properly.

Find USB serial crashed. Added __init__.py to src and src/scripts to fix. Output might not be right either, needs review.

Need to implement test power on, current tries to run tester.sh

### Integral Menu
Find integral serial reports matches and stops output.

Uses wrong script dir path. Currently set to use the copied shell script from the project instead of the local/scripts on the device. 
Fixed script path, works properly.

### Dock Menu
Everything works as expected!
Single HD dock config, need to test with more complex setups.

### Touch Menu
UPDD menu seems to work. Set appropriate defaults. Need to update the crontab system and test with a device actually using UPDD driver.

### Other Defaults Menu
Magewell and max browsers works.

Set headphones faied. Probably because its just a mini without the headphones plugged in...

All the others seem to be working well. Tested Multisite Enterprise and it worked, haven't tested with SMB.

