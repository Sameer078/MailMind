from pymongo import MongoClient
import os

# Connect to MongoDB
client = MongoClient(os.getenv("MONGODB_URL"))
db = client[os.getenv("MONGODB_DATABASE")]
collection = db[os.getenv("MONGODB_COLLECTION")]

def scam_score(sender_email):
    total_count = collection.count_documents({"email_metadata.from": sender_email})
    scam_count = collection.count_documents(
        {"email_metadata.from": sender_email, "scam_status": "SCAM"}
    )
    scam_score = scam_count / total_count if total_count > 0 else 0.0
    return {
        "scam_score": round(scam_score, 3),
        "total_count": total_count,
        "scam_count": scam_count,
    }

def save_mail(email_doc):
    # Insert into collection
    result = collection.insert_one(email_doc)
    return result