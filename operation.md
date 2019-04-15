
### mini_CPC operation instrunction


Yusheng Wu

yusheng.wu@helsinki.fi

tel: 00358 41 4722694 (FI)

tel: 0086 132 69358090 (CN)

2019-04-15

-------------------------------------


##### Linux terminal commands:
`pwd`: show current absolute path

`cd`: go to a directory

`cd ~`: go to home directory

`cd ..`: back to parent directory

`ls`: files are in the directory you are in

`sudo:` root user.

##### go to directory `~/mini_cpc/`
mini_CPC python software script is in `~/mini_CPC/`. Run: `cd mini_CPC`

##### run python script
In `~/mini_CPC/`, Run: 'sudo python mini_cpc_V0.3.py' to start software).

##### quit python
'Ctrl + C' will stop python running, but it will not clean Raspberry Pi Input/Output status. So if one is not going to shun down the Raspberry Pi, should use configuration file to quit python.

##### modify configuration file
Configuration file is also in `~/mini_CPC/`. Run: `sudo nano conf.ini` to open the file with a text editor. Change `working = T` to `F` and save. Here should be change back to `T` before running pytho nnext time. One can also change other parameters this way in the `conf.ini` file.