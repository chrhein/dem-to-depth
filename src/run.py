import ast
import json
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
)
from werkzeug.utils import secure_filename
from image_handling import get_exif_data, reduce_filesize, transform_panorama
from renderer import render_dem
from tools.file_handling import make_folder
from PIL import Image


def create_app():
    app = Flask(__name__, static_url_path="/src/static")
    UPLOAD_FOLDER = "src/static/"
    app.secret_key = "secret key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

    @app.route("/", methods=["POST", "GET"])
    def homepage():
        session["pano_path"] = ""
        session["render_path"] = ""
        session["render_coords"] = ""
        session["pano_coords"] = ""
        return render_template("upload_pano.html")

    @app.route("/upload", methods=["POST", "GET"])
    def upload():
        if request.method == "POST":
            f = request.files["file"]
            filename = secure_filename(f.filename)
            pano_path = f"{UPLOAD_FOLDER}{filename}"
            make_folder(UPLOAD_FOLDER)
            f.save(pano_path)
            reduce_filesize(pano_path)
            with Image.open(pano_path) as img:
                width, _ = img.size
                if width > 16384:
                    return "<h4>Image is too wide. Must be less than 16384px.</h4>"
                img.close()
            has_location_data = get_exif_data(pano_path)
            if not has_location_data:
                return "<h4>Image does not have location data.</h4>"
            session["pano_path"] = pano_path
            return redirect(url_for("spcoords"))

    @app.route("/rendering")
    def rendering():
        pano_path = session.get("pano_path", None)
        render_path = session.get("render_path", None)
        render_complete = render_dem(pano_path, 2, "", render_filename=render_path)
        if render_complete:
            return ("", 204)
        else:
            return "<h4>Render Failed</h4>"

    # select pano coordinates
    @app.route("/spcoords")
    def spcoords():
        pano_path = session["pano_path"]
        pano_filename = f"{pano_path.split('/')[-1].split('.')[0]}"
        render_path = f"{UPLOAD_FOLDER}{pano_filename}-render.png"
        session["render_path"] = render_path
        with Image.open(pano_path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 360 / (width / height) - 30
        vertical_fov = 180 / (width / height) - 25
        return render_template(
            "pano_select_coords.html",
            pano_path=pano_path,
            render_path=render_path,
            pwidth=width,
            pheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
        )

    # get pano selectec coordinates
    @app.route("/gpsc", methods=["POST"])
    def gpsc():
        if request.method == "POST":
            pano_coords = request.form.get("panoCoords")
            pano_coords = ast.literal_eval(pano_coords)
            session["pano_coords"] = pano_coords
            app.logger.info(f"pano_coords: {pano_coords}")
            render_path = session.get("render_path", None)
            return redirect(
                url_for(
                    "srcoords",
                    render_path=render_path,
                )
            )
        return ("", 404)

    # select render coordinates
    @app.route("/srcoords")
    def srcoords():
        render_path = session.get("render_path", None)
        with Image.open(render_path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 360
        vertical_fov = 115
        return render_template(
            "render_select_coords.html",
            render_path=render_path,
            rwidth=width,
            rheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
        )

    # get render selected coordinates
    @app.route("/grsc", methods=["POST"])
    def grsc():
        if request.method == "POST":
            render_coords = request.form.get("renderCoords")
            render_coords = ast.literal_eval(render_coords)
            session["render_coords"] = render_coords
            app.logger.info(f"render_coords: {render_coords}")
            return redirect(url_for("transform"))

    @app.route("/transform")
    def transform():
        pano_path = session.get("pano_path", None)
        render_path = session.get("render_path", None)
        pano_coords = str(session.get("pano_coords", None))
        render_coords = str(session.get("render_coords", None))
        transform_panorama(pano_path, render_path, pano_coords, render_coords)
        return ("", 204)

    """ @app.route("/testing")
    def testing():
        raw_coords = request.args.get("render_selected_coordinates")
        render_selected_coordinates = json.loads(raw_coords)
        app.logger.info(render_selected_coordinates)
        return ("", 204) """

    return app


if __name__ == "__main__":

    """pano_path = "src/static/panorama1.jpg"
    render_path = "src/static/panorama1-render.png"
    pano_coords = "[[1286.8924817408247, 127.35575452483627], [845.2103367504903, 199.94802861739322], [756.5816809492201, 134.7696987596589], [410.63766318325224, 71.95208202296402]]"
    render_coords = "[[274.39006324293285, 367.5188668909752], [85.15999074062833, 401.8913696460148], [32.114775209471205, 366.52459835992335], [1334.6563210168401, 344.32867980734034]]"
    transform_panorama(pano_path, render_path, pano_coords, render_coords)
    exit()"""

    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
