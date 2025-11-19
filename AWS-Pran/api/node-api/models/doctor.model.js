import mongoose from "mongoose";

const doctorSchema = new mongoose.Schema(
  {
    name: { type: String, required: true },
    image: { type: String, required: true },
    specialty: { type: String, required: true },
    experience: { type: Number, required: true },
    contactNo: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    gender: { type: String, enum: ["Male", "Female", "Other"], required: true },
    location: { type: String, required: true },
    qualifications: { type: String, required: true },
    workingHours: { type: String, required: true }, // Example: "9 AM - 5 PM"
    fees: { type: Number, required: true },
  },
  { timestamps: true }
);

const Doctor = mongoose.model("Doctor", doctorSchema);

export default Doctor;
