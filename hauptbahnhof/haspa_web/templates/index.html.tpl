<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Hackerspace: #state#</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
      /* latin */
      @font-face {
        font-family: 'Josefin Slab';
        font-style: normal;
        font-weight: 100;
        src: local('Josefin Slab Thin'), local('JosefinSlab-Thin'), url(css/josefinslab-thin.woff2) format('woff2'), url(css/josefinslab-thin.woff) format('woff');
        unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2212, U+2215, U+E0FF, U+EFFD, U+F000;
      }
      /* latin */
      @font-face {
        font-family: 'Josefin Slab';
        font-style: normal;
        font-weight: 400;
        src: local('Josefin Slab'), local('JosefinSlab'), url(css/josefinslab.woff2) format('woff2'), url(css/josefinslab.woff) format('woff');
        unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2212, U+2215, U+E0FF, U+EFFD, U+F000;
      }

      * {
        transition: all 0.3s ease;
      }

      html, body {
        height: 100%;
        width: 100%;
        margin: 0;
        padding: 0;
        font-family: "Josefin Slab", serif;
        font-weight: 100;
      }

      body {
	position: relative;
      }

      body.offen {
        background: #55ee33;
      }
      body.geschlossen {
        background: #ee5555;
      }

      div {
        position: absolute;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
      }

      .offen div:before {
        content: "Offen";
        font-size: 25vw;
      }
      .geschlossen div:before {
        content: "Geschlossen";
        font-size: 15vw;
      }

      span {
        position: absolute;
        bottom: 0.5em;
        left: 0;
        right: 0;
        text-align: center;
        font-weight: 500;
      }
    </style>
  </head>
  <body class="#state#">
    <div>
    </div>
    <span id="last_update">
        Letzte Aktualisierung: #last_update#
    </span>

    <script>
      function fetchJSONFile(path, callback) {
          var httpRequest = new XMLHttpRequest();
          httpRequest.onreadystatechange = function() {
              if (httpRequest.readyState === 4) {
                  if (httpRequest.status === 200) {
                      var data = JSON.parse(httpRequest.responseText);
                      if (callback) callback(data);
                  }
              }
          };
          httpRequest.open('GET', path);
          httpRequest.send();
      }

      setInterval(function() {
        fetchJSONFile('current.json?time=' + Math.floor(Date.now() / 1000), function(data){
          document.body.className = data.state;
          document.getElementById('last_update').innerHTML = 'Letzte Aktualisierung: ' + data.last_update;
        });
      }, 4200);
    </script>
  </body>
</html>
