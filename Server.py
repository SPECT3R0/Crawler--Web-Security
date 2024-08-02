from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# HTML content that will be updated
content = ["First content", "Second content"]

# HTML template with embedded JavaScript
html_template = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Dynamic Content</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.7.1/jquery.min.js" integrity="sha512-v2CJ7UaYy4JwqLDIrZUI/4hqeoQieOmAZNXBeQyjo21dadnwR+8ZaIJVT8EE2iyI61OV8e6M8PP2/4hpQINQ/g==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
    <script type="text/javascript">
      document.addEventListener('DOMContentLoaded', function() {
        const contentElement = document.getElementById('content');
        let changeCount = 0;
        const maxChanges = 5;
        const updateInterval = 20000; // 20 seconds
        const logInterval = 25000; // 25 seconds
        const logMessage = 'JavaScript code updated dynamically.';

        function fetchContent() {
          fetch('/update')
            .then(response => response.json())
            .then(data => {
              contentElement.textContent = data;
            });
        }

        function startUpdating() {
          if (changeCount < maxChanges) {
            fetchContent();
            changeCount++;
            setTimeout(startUpdating, updateInterval);
          }
        }

        function addConsoleLog() {
          setInterval(function() {
            // Dynamically create and inject a script with a console log
            const script = document.createElement('script');
            script.textContent = console.log(logMessage);
            document.head.appendChild(script);
          }, logInterval);
        }

        // Start updating and adding console log after page loads
        startUpdating();
        addConsoleLog();
      });
    </script>
  </head>
  <body>
    <h1 id="content">Loading...</h1>
  </body>
</html>
"""

# Route for the main page
@app.route('/')
def index():
    return render_template_string(html_template)

# Route for fetching updated content
@app.route('/update')
def update():
    global content
    content[0], content[1] = content[1], content[0]  # Swap content
    return jsonify(content[0])

# Main driver function
if __name__ == '__main__':
    app.run(debug=True)
