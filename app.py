from flask import Flask, render_template, request, redirect
import model

app = Flask(__name__)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('page_not_found.html'), 404

@app.route("/")
def index():
    warnings = model.get_warnings()
    if warnings == None or warnings == False or len(warnings) == 0:
        warnings = None
    return render_template("index.html", warnings=warnings, licenses=model.retrieveLicData())

@app.route("/results",  methods=['GET', 'POST'])
def route_all():
    report = model.Report(test='all')
    if request.method == 'GET':
        return render_template("results.html", data=report.get_data(), type="All", headers=report.get_headers())
    if request.method == 'POST':
        report.write_rpt()
        return render_template("results.html", data=report.get_data(), type="All", headers=report.get_headers(), message = 'Report Downloaded Successfully')

@app.route('/edit',  methods=['GET', 'POST'])
def edit():
    if request.method == 'GET':
        data=model.get_Licenses_Id_from_Db()
        return render_template("edit.html",license=None, data=data)
    if request.method == "POST":
        license = request.form['License']
        report = model.Report(test='License',License=license)
        if report.error == False:
            return render_template("edit.html",rHeaders=report.headers['Reputation'], lHeaders=report.headers['LicenseData'], rData=report.data['Reputation'], lData=report.data['LicenseData'])
        else:
            return render_template("edit.html", license=None)

@app.route("/results/<type>",  methods=['GET', 'POST'])
def route(type):
    report = model.Report(test='results', type=type)
    if request.method == 'GET':
        return render_template("results.html", data=report.get_data(), type=type, headers=report.get_headers())
    if request.method == 'POST':
        report.write_rpt()
        return render_template("results.html", data=report.get_data(), type=type, headers=report.get_headers(), message = 'Report Downloaded Successfully')


@app.route('/edit/<id>',  methods=['GET','POST'])
def db_edit(id):
    table=id.split('-')[0]
    tblid=id.split('-')[1]
    report = model.Report(test='Edit', id=tblid, table=table)
    formaction = "/post/{}".format(id)
    if request.method == 'GET':
        return render_template("editdb.html", data=report.data, table=table,tblid=tblid, formaction=formaction)

@app.route('/post/<id>', methods=['POST'])
def process(id):
    table=id.split('-')[0]
    tblid=id.split('-')[1]
    newLicense= request.form['NewLicense']
    Term = request.form['Term']
    Ignore = request.form['Ignore']
    name =  request.form['Name']
    if newLicense == 'False':
        newLicense = False
    if Term == 'False':
        Term = False
    if Ignore == 'False':
        Ignore == ''
    if name == 'False':
        name == False

    LIC = model.get_license_from_id(tblid)
    model.edit_reputation(LIC, new_license = newLicense, term=Term, Ignore=Ignore,Name=name )

    return redirect('/')


@app.route('/add', methods=['POST'])
def add_entry():
    try:
        id = request.form['License']
        id=str(id)
        model.edit_reputation(id, init=True)
        model.dit_licenseData(id, init=True, DataDate=model.now)
    except:
        pass
    return redirect('/edit')

if __name__=="__main__":
    model.data_check()
    app.run(debug=True)
