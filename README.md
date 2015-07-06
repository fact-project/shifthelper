# FACT shift helper

* Calls you via skype if security limits are
reached, data taking stopped or the QLA exceeds alert limits

* just enter your phone number, check for the incoming
call

* go to bed

You can give the number directly as firs command line option

## Why is this a private repo?

Because in the code there are login credentials to our RunInfo DB.
While the information stored in our RunInfo DB are public by design, the access
to this DB using this read-only user is **not** to be considered safe.
