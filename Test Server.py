from flask import Flask, render_template_string
import random

app = Flask(__name__)

# List of movie websites (used for ad links)
movie_websites = [
    'https://www.getsmartyapp.com/landers/lander39.php?sid=08062024_admaven39int_880166&clkid=6140449129754221484&cid=lander39&partner=admaven',
    'https://1fichier.com/?uq5uahrfdqdrhxh68x00',
    'https://clickndownload.link/y0lk3wfcbyi3',
    'https://desiupload.co/0qye9v71swlw',
    'https://fikper.com/q84DNF7Nan/Volshebniki+(2022)+Dual+Audio+Hindi+ORG+720p+WEB-DL.mkv.html',
    'https://full4movies.dog/',
    'https://streamblasters.cc/',
    'https://isaimini.tokyo/'
]

@app.route('/')
def index():
    html_content = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Single Page Application</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            nav {
                background-color: #333;
                color: #fff;
                padding: 10px 0;
                z-index: 1;
                position: relative;
            }
            ul {
                list-style: none;
                display: flex;
                justify-content: center;
                margin: 0;
                padding: 0;
            }
            li {
                margin: 0 15px;
            }
            a {
                color: #fff;
                text-decoration: none;
                font-size: 18px;
            }
            section {
                display: flex;
                flex-wrap: wrap;
                justify-content: space-around;
                padding: 20px;
            }
            .card {
                background-color: #f4f4f4;
                border: 1px solid #ddd;
                border-radius: 8px;
                width: 200px;
                margin: 20px;
                text-align: center;
                padding: 10px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                cursor: pointer;
                position: relative;
            }
            .card img {
                width: 100%;
                border-radius: 8px;
                cursor: pointer;
            }
            .card button {
                background-color: #333;
                color: #fff;
                border: none;
                padding: 8px;
                border-radius: 5px;
                cursor: pointer;
                margin-top: 10px;
            }
            /* Styles for dynamic ads */
            .dynamic-ad {
                position: fixed;
                bottom: 20px;
                right: 20px;
                background-color: #fff;
                border: 1px solid #ddd;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                padding: 10px;
                width: 300px;
                z-index: 1000;
                display: none; /* Initially hidden */
            }
            .dynamic-ad button {
                background-color: #333;
                color: #fff;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>

        <!-- Navbar -->
        <nav id="navbar">
            <ul>
                <li><a href="#" id="navbar-link1">Home</a></li>
                <li><a href="#" id="navbar-link2">Genre</a></li>
                <li><a href="#" id="navbar-link3">Country</a></li>
            </ul>
        </nav>

        <!-- Categories Section -->
        <section id="categories">
            <div class="card">
                <img src="https://via.placeholder.com/200x150" alt="Category 1" id="card-img1">
                <button id="card-btn1">Learn More</button>
            </div>
            <div class="card">
                <img src="https://via.placeholder.com/200x150" alt="Category 2" id="card-img2">
                <button id="card-btn2">Learn More</button>
            </div>
            <div class="card">
                <img src="https://via.placeholder.com/200x150" alt="Category 3" id="card-img3">
                <button id="card-btn3">Learn More</button>
            </div>
            <div class="card">
                <img src="https://via.placeholder.com/200x150" alt="Category 4" id="card-img4">
                <button id="card-btn4">Learn More</button>
            </div>
            <div class="card">
                <img src="https://via.placeholder.com/200x150" alt="Category 5" id="card-img5">
                <button id="card-btn5">Learn More</button>
            </div>
            <div class="card">
                <img src="https://via.placeholder.com/200x150" alt="Category 6" id="card-img6">
                <button id="card-btn6">Learn More</button>
            </div>
        </section>

        <!-- Dynamic Ad Container -->
        <div id="dynamic-ad" class="dynamic-ad">
            <p>Special Offer! Don't miss out on the latest movies.</p>
            <button onclick="window.open(getRandomMovieWebsite(), '_blank')">Check it out</button>
        </div>

        <script>
            // List of movie websites
            const movieWebsites = {{ movie_websites | safe }};

            function getRandomMovieWebsite() {
                return movieWebsites[Math.floor(Math.random() * movieWebsites.length)];
            }

            const navbarLinks = ['navbar-link1', 'navbar-link2', 'navbar-link3'];
            const cardImages = ['card-img1', 'card-img2', 'card-img3', 'card-img4', 'card-img5', 'card-img6'];
            const cardButtons = ['card-btn1', 'card-btn2', 'card-btn3', 'card-btn4', 'card-btn5', 'card-btn6'];

            function addEventListenersToElements(elements) {
                elements.forEach(id => {
                    document.getElementById(id).addEventListener('click', function() {
                        window.open(getRandomMovieWebsite(), '_blank');
                    });
                });
            }

            addEventListenersToElements(navbarLinks);
            addEventListenersToElements(cardImages);
            addEventListenersToElements(cardButtons);

            document.addEventListener('click', function(event) {
                const navbar = document.getElementById('navbar');
                const cards = document.querySelectorAll('.card');
               
                if (!navbar.contains(event.target) && !Array.from(cards).some(card => card.contains(event.target))) {
                    window.open(getRandomMovieWebsite(), '_blank');
                }
            });

            // Function to show a dynamic ad after a few seconds
            function showDynamicAd() {
                const dynamicAd = document.getElementById('dynamic-ad');
                dynamicAd.style.display = 'block'; // Show the ad

                setTimeout(() => {
                    dynamicAd.style.display = 'none'; // Hide the ad after 10 seconds
                }, 10000);
            }

            // Show dynamic ad after 5 seconds
            setTimeout(showDynamicAd, 5000);
        </script>

    </body>
    </html>
    '''
    return render_template_string(html_content, movie_websites=movie_websites)

if __name__ == '__main__':
    app.run(debug=True)
