from flask import Flask, render_template, request, redirect
import model

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html", warnings=model.get_warnings(), licenses=model.retrieveLicData())

@app.route("/results")
def route_all():
    return render_template("results.html", data=model.qry_results(), type="All")

@app.route("/results/<type>")
def route(type):
    return render_template("results.html", data=model.qry_results(type), type=type)

@app.route('/edit')
def edit():
    return render_template("edit.html")

@app.route("/postentry", methods=["POST"])
def postentry():
    name = request.form["name"]
    message = request.form["message"]
    model.add_entry(name, message)
    return redirect("/")

if __name__=="__main__":
    model.data_check()
    app.run(debug=True)
