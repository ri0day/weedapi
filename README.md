# weedapi
seaweedfs http api add jwt authentication 

```
│  gen_conf.sh #configure file generator
│  README.md  readme
│
├─api
│      test_weed_api_delete.py
│      test_weed_api_read.py
│      test_weed_api_update.py
│      test_weed_api_upload.py
│      weed_api.py          #http api 
│
└─bin
        weed  #seaweedfs binary file

```

#how to play
change the ip address setting ,suit yours 
1. install weedfs master and volume
2. pip2.7 install requirements.txt
3. cd api
4. python weed_api.py