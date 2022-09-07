# SauronX installation

## Supported operating systems

SauronX requires some specific OS and hardware configuration, including
things like power settings. This makes it difficult to know which
OS distributions and versions are compatible.
We have successfully run SauronX on Ubuntu 20.04, Ubuntu 18.04, and Windows 10.
Only Ubuntu 20.04.x is currently actively supported.
SauronX specifically will not function correctly in Mac OS X due to compatibility
with the Spinnaker SDK. To summarize:

| OS                  | Compatibility      |
| ------------------- | ------------------ |
| Ubuntu 20.10        | :grey_question: |
| Ubuntu 20.04.x LTS  | :white_check_mark: |
| Ubuntu 18.04.x LTS  | :heavy_check_mark: |
| other Linux         | :grey_question: |
| Windows 10          | :grey_question: |
| Mac OS X            | :x: |


## Install Linux

Install Ubuntu 20.04.
Change the UEFI/BIOS settings so that you boot from the drive. Follow the instructions that show up
to install Linux.

**IMPORTANT**: I faced this issue when installing the Linux OS onto the Samsung EVO/SSD drives:
`Unable to install GRUB`. Try the following things in the UEFI interface to resolve this issue:

- Make sure Fast Boot is Disabled.
- Make sure Secure Boot is Disabled. Also, check to see if CSM/Legacy options is disabled.
- Manually install the bootloader (not recommended).

Also, take a look at this [page](http://www.rodsbooks.com/linux-uefi/) for troubleshooting.

## Install necessary Linux Packages

Open a terminal and enter the following commands to install the necessary packages:
`sudo apt update`
`sudo apt upgrade`
`sudo apt install python3 git vim `
`sudo apt install libasound2-dev portaudio19-dev`

Install ZSH and Oh-my-zsh:
`sudo apt install zsh`
`sudo chsh -s /usr/bin/zsh root`

```
sh -c "$(wget -O- https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
```

## SSH setup

If your database lives on another server (recommended), I recommend setting up SSH keys.
SauronX will use rsync to transfer data, and you don't want to get prompted each time.
You should also up an SSH tunnel to the database.
This alias will do it, so add it to `~/.zshrc`:
```
alias tunnel="ssh -L 1492:localhost:3306 valinor.ucsf.edu"
```
Change the hostname and make sure the local port (1492) matches the one in your valarpy config.

Run `ssh-keygen` to generate your keys and run `ssh-copy-id sauronx{INSERT_NUM}@valinor.ucsf.edu`.

## Install Sauronx

Run `pip install sauronx`.
I recommend using [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

## Install Arduino
Download the Arduino Software from [here](https://www.arduino.cc/en/Main/Donate).
After you extract the arduino directory, navigate to the arduino directory and run:

`./arduino-linux-setup.sh $USER` where `$USER` is the main user on your machine.

## Building FFmpeg
SauronX uses hardware accelerated parameters for ffmpeg so it's critical that you build ffmpeg from
source. Follow the instructions
[here](https://www.intel.com/content/dam/www/public/us/en/documents/white-papers/quicksync-video-ffmpeg-install-valid.pdf).
Install the media-sdk 19.4.0 by unzipping the `MediaStack.tar.gz`.
Follow the instructions on building ffmpeg in the link above.

## Install Camera Spinnaker SDK
Download the SDK from [here](https://www.flir.com/products/spinnaker-sdk/) and download from the
right ubuntu directory.
Extract the `spinnaker-1.26.0.31-Ubuntu18.04-amd64-pkg.tar.gz` file. Follow the directions in the
**README.md** (found in the extracted directory `spinnaker-1.26.0.31-Ubuntu18.04-amd64/README.md)`
to finish installation of Spinnaker. Make sure to add the main user to flirimaging group when it
asks you. Follow the instructions for modifying the USB-FS memory.

**NOTE:** We have not tested SauronX against the new 2.0 version of Spinnaker.

The main sections to follow in the README.md are the following;
- Install dependencies listed on Section 1.
- Install Spinnaker via Section 2.
- Modify the USB-FS Memory via Section 3.
- Increase Receive Buffer size via Section 4.2

### Compile Spinnaker scripts
Navigate to the `/usr/src/spinnaker/src` directory.
Make the following directories: `Acquisition_sx` and `snapshot_sx`.
These directory paths should be the same as the paths listed under the [local.executables]
section of the `~/sauronx.toml` file.

Navigate to the Spinnaker directory in the sauronx repo.
Copy the `sauronx/spinnaker/Acquisition/Acquisition_sx.cpp` file to the
`/usr/src/spinnaker/src/Acquisition_sx` directory. Then, copy all the files in the `Acquisition`
(example) directory to the `Acquisition_sx` directory. Remove the example Acquisition.cpp script that is copied over.
Do the same for the `snapshot_sx` file.
```
sudo mkdir /usr/src/spinnaker/src/Acquisition_sx
sudo mkdir /usr/src/spinnaker/src/snapshot_sx
sudo cp -r /usr/src/spinnaker/src/Acquisition/* /usr/src/spinnaker/src/Acquisition_sx
sudo cp ~/sauronx/spinnaker/Acquisition/Acquisition_sx.cpp /usr/src/spinnaker/src/Acquisition_sx/
sudo rm /usr/src/spinnaker/src/Acquisition_sx/Acquisition.cpp
sudo cp -r /usr/src/spinnaker/src/Acquisition/* /usr/src/spinnaker/src/snapshot_sx
sudo cp ~/sauronx/spinnaker/Snapshot_SX/snapshot_sx.cpp /usr/src/spinnaker/src/snapshot_sx
sudo rm /usr/src/spinnaker/src/snapshot_sx/Acquisition.cpp
```
Edit the MakeFile. Change the following lines:
 - `OUTPUTNAME = Acquisition${D}` → `OUTPUTNAME = Acquisition_sx${D}`
 - `\_OBJ = Acquisition.o` → `\_OBJ = Acquisition_sx.o`
Then, run make. Repeat this for the snapshot_sx file.
 - `OUTPUTNAME = Acquisition${D}` -> `OUTPUTNAME = snapshot_sx${D}`
 - `\_OBJ = Acquisition.o` → `\_OBJ = snapshot_sx.o`

```
cd /usr/src/spinnaker/src/Acquisition_sx
vim MakeFile #Make the edits above.
sudo make
```

Make sure both scripts successfully make. Write down the path to each made software under the
[local.executables] section in your toml file.
```
[local.executables]
pointgrey_acquisition = "/usr/src/spinnaker/bin/Acquisition_sx"
pointgrey_snapshot = "/usr/src/spinnaker/bin/snapshot_sx"
```

## Configure db connection

You will need to have [Valar](https://github.com/dmyersturnbull/valar) set up.

Use [valarpy](https://github.com/dmyersturnbull/valarpy) for the database connection.
The [sauronlab](https://github.com/dmyersturnbull/sauronlab) setup
happens to be the simplest way to do this.
Run:

```bash
pip install git+https://github.com/dmyersturnbull/sauronlab.git/main[perf,extras]
sauronlab init
```

## Install and configure SauronX

Then run install SauronX and generate a skeleton configuration with:

```bash
pip install git+https://github.com/dmyersturnbull/sauronx.git/main
sauronx init
```

Then, edit the generated config file as needed.


## Mount additional drive

Create a directory at `~/frames`. Follow directions
[here](https://confluence.jaytaala.com/display/TKB/Mount+drive+in+linux+and+set+auto-mount+at+boot)
to mount the extra disk automatically on boot. After you reboot, run this command:
```
sudo chmod -R 777 ~/frames
```
This will allow for the writing of frames into this directory when sauronx is running.

## Additional changes to make
There are still some additional changes you have to make.

### Configure Sound
Go to Settings > Sound > Sound Effects and set Alert Volume to OFF.

### Disable Auto-Suspend.
Follow the instructions on
[here](https://websiteforstudents.com/suspend-ubuntu-18-04-lts-beta-desktop-automatically-after-inactivity/)
to disable auto-suspend.

### Turn off usb-suspension
This is necessary so that the camera isn’t auto disconnected.
```
sudo sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="/&usbcore.autosuspend=-1 /' /etc/default/grub
sudo update-grub
systemctl reboot
```
Once the computer reboots, the following command should return -1
```
cat /sys/module/usbcore/parameters/autosuspend
```

### Turn off suspending of audio modules after idleness
Comment out the line that says `load-module module-suspend-on-idle` and the line that says
`load-module module-switch-on-port-available` in `/etc/pulse/default.pa`.

```
sudo vim /etc/pulse/default.pa
```
Also, add the following section to the bottom of the `default.pa` file:
```### Set Default Card Profile
set-card-profile 1 output:analog-stereo+input:analog-stereo
```
Then, do the following to reset the audio:
```
killall pulseaudio
```
## Set up SSH to allow remote logins
Install ssh to allow for remote logins.
```
sudo apt update
sudo apt install openssh-server
sudo ufw allow 22
```
You should look into obtaining static IP addresses for the machine if you'd like to be able to
consistently ssh into it.

## Arduino Issues
If you’re getting `Permission Denied` errors even after adding yourself to the `dialout` group,
add a rule that gives you permissions:
```
sudo vim /etc/udev/rules.d/arduinorule.rules
# add the line
KERNEL=="ttyACM0", MODE="0666"
```

## [OPTIONAL] Sudo prompts
SauronX has certain calls that require sudo privileges (camera acquisition and ffmpeg usage).
Add a line in to the `/etc/sudoers` file that allows your user to have root privileges without
password prompts. Refer to this
[sudoers guide](https://www.cyberciti.biz/faq/how-to-sudo-without-password-on-centos-linux/) a link.
