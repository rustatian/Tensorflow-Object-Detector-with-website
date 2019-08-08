# Tensorflow Object Detector with website
Website with image recognition from camera

To work with object detector you must:
1. Get certificate files and add to tornado web server in mainWorker.py file
   - Path to folder - data_dir
   - Add .crt and .key files
2. In file server.js:
   - Add ca-bundle, key and crt files
3. In file receiver.js:
   - Add your wss enpoint address (for example -  wss://example.com:443)
4. Run npm install in folder 'browser/server'

After all done, run object recognizer in you browser:
-sudo python3 mainWorker.py
-sudo nodejs server.js (in folder <browser/server>)

