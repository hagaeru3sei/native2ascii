# native2ascii

### Overview

Property file management tool

### Setup

Install node libraries and python3 bottle

```
cd $projectRoot
npm install
pip3 install bottle
```

### Configuration

For Python API
- src/res/default.ini

For js client
- src/js/config.js.sample

### Build

```
npm run build
```

### Running test app

```
cp src/js/config.js.sample src/js/config.js
npm run www
```
access to http://localhost:8000

### Start API

```
cp src/res/default.ini src/res/settings.ini
npm start
```

### Test

```
npm test
```

