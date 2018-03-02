// modules
var express = require('express')
  , https = require('https')
  , fs = require('fs')
  , morgan = require('morgan');

var options = {
  ca: fs.readFileSync(‘filename.ca-bundle'),
  key: fs.readFileSync(‘filename.key'),
  cert: fs.readFileSync(‘filename.crt'),
}

// configuration files
var configServer = require('./lib/config/server');

// app parameters
var app = express();
app.set('port', configServer.httpPort);
app.use(express.static(configServer.staticFolder));
app.use(morgan('dev'));

// serve index
require('./lib/routes').serveIndex(app, configServer.staticFolder);

// HTTP server
var server = https.createServer(options, app);
server.listen(app.get('port'), function () {
  console.log('HTTP server listening on port ' + app.get('port'));
});

// WebSocket server
var io = require('socket.io')(server, { origins: '*:*'});
io.on('connection', require('./lib/routes/socket'));

module.exports.app = app;
