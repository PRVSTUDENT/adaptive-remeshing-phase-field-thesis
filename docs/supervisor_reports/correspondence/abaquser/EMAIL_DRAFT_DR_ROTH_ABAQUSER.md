# Ready-to-Send Email Draft: IMFD ABAQUSER Access Request

**To:** Dr.-Ing. Stephan Roth (stephan.roth@imfd.tu-freiberg.de)  
**Cc:** Prof. Dr. Bjoern Kiefer (bjoern.kiefer@imfd.tu-freiberg.de)  
**From:** Pruthvirajsinh Padhiyar (pr21vyci / pruthvirajsinh.padhiyar@student.tu-freiberg.de)  
**Date:** September 23, 2026  
**Subject:** Master Thesis Task 6: Request for Authentic IMFD ABAQUSER Tool / Cluster Access

---

```text
Subject: Master Thesis Task 6: Request for Authentic IMFD ABAQUSER Tool / Cluster Access

Dear Dr. Roth,

I hope this email finds you well.

In the context of my Master Thesis ("Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements" under the supervision of Prof. Dr. Kiefer and yourself), I am currently working on Thesis Task 6 (Gate 7): "Integration of the ABAQUSER visualization tool, developed at IMFD, into the modeling framework."

We have successfully established and verified an internal in-solver companion visualization bridge (confirming zero parasitic stiffness across 7,028 solver increments in job 1400408.mmaster02). However, to formally complete Task 6 and adhere to the proposal requirements and published literature (Roth et al., GACM Report 5, 2012/2014; Diddige, Roth, Kiefer, CMAME 2025), we want to integrate and benchmark against the authentic IMFD ABAQUSER tool.

I performed an inventory of the TU Freiberg HPC cluster environment (login.hpc.tu-freiberg.de), but did not find a runnable distribution in the accessible module system (module spider abaquser) or shared application paths. Furthermore, the directory /projects/imfd is permission-restricted for my student account (pr21vyci).

Could you please provide access to the authentic ABAQUSER tool (or let me know its location on the cluster / git repository), along with:
1. Brief execution/invocation instructions (e.g. CLI command syntax and supported Abaqus/Python versions);
2. Required input file format and interface conventions;
3. Expected UEL output/state-variable formatting conventions;
4. A minimal sample input/output example for initial testing, if available.

Once the authentic ABAQUSER implementation and its interface instructions are provided, I will integrate it with the existing verified Mode-I benchmark according to the documented input/output requirements and perform the minimum necessary verification.

Thank you very much for your guidance and support.

Best regards,

Pruthvirajsinh Padhiyar
Master Thesis Candidate
Institute of Mechanics and Fluid Dynamics (IMFD)
TU Bergakademie Freiberg
```
