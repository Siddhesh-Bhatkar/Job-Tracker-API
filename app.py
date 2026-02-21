from flask import Flask, request, jsonify 
from extensions import db
from models import Job


app = Flask(__name__)  #__name__ is used : to help flask determine the root path of application

#Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

#Route
@app.route('/')
def home():
    return {"message": "Job Tracker API is running"}

@app.route('/jobs', methods=['POST'])
def add_job():
    data = request.get_json()

    allowed_statuses = ["Applied", "Interview", "Rejected", "Offer"]

    status_value = data.get("status", "Applied")

    if status_value not in allowed_statuses:
       return jsonify({"error": "Invalid status value"}), 400

    
    new_job = Job(
        company_name=data["company_name"],
        role=data["role"],
        status = data.get("status","Applied"),
        notes=data.get("notes")
    )
    db.session.add(new_job)
    db.session.commit()
    
    return jsonify(new_job.to_dict()),201

@app.route('/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    job = Job.query.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    data = request.get_json()

    job.company_name = data.get("company_name", job.company_name)
    job.role = data.get("role", job.role)
    job.status = data.get("status", job.status)
    job.notes = data.get("notes", job.notes)

    db.session.commit()

    return jsonify(job.to_dict())

@app.route('/jobs', methods=['GET'])
def get_jobs():
    status = request.args.get("status")

    if status:
        jobs = Job.query.filter_by(status=status).all()
    else:
        jobs = Job.query.all()

    return jsonify([job.to_dict() for job in jobs])


@app.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    job = Job.query.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    db.session.delete(job)
    db.session.commit()

    return jsonify({"message": "Job deleted successfully"})



#Server
if __name__ == '__main__':
    app.run(debug=True)