phablet-tools
=============

Abstract
---------
This is the modified version of phablet-tools based on Augest 06, 2013 version (`phablet-tools_0.15+13.10.20130806`).

The original version is http://ppa.launchpad.net/phablet-team/tools/ubuntu/pool/main/p/phablet-tools/

Phablet-tools is a tool for installing the Ubuntu Touch OS into your mobile devices (Currently, only Nexus S, Nexus 4, Nexus 7 and Nexus 10 are supported officially)

Motivation
----------

Now Phablet-tools only can run on the Ubuntu, it is, somehow, inconvenient for guys who can not access Ubuntu, like me, I only can use Windows 7 in my office. 

So I tried to read the source code to find out whether it can be ported to other systems, like Windows. And I found it is made by Python 2.X, and it is almost platform-independent.

I modified a little code in the  phabletutils/environment.py, and setup this repository, I hope it can be helpful for the guys who want to try Ubuntu Touch without Ubuntu System , I know it sounds some-kind weird, ;-).

Requirement
-----------

Because Phablet-tools need some dependencies, you need install them by yourself.

1. Python 2.X, I recommend you to install 2.7, I just test it on 2.7.5.
2. ADB tools (including adb.exe and fastboot.exe, I think it will not be a problem for you)
3. wget and rsync, it need to be installed on Windows, and for Mac, it seems it is out of box. (I am not sure since I installed MacPorts)
4. USB drivers for your device, I believe it will not be another problem for you, just google it.

Remember, all of them need to be added into PATH environment variable.

For Python, it need requests and configobj modules, you can install them use `ez_setup` tools.

Install 
--------
Please refer to this link https://wiki.ubuntu.com/Touch/Install
