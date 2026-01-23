################################

To generate data, run:

src/secret.py gen parameters.json

(generated model and sequence written to destinations provided in parameters.json)

################################


To mine rules, run:

src/secret.py mine parameters.json sequences.txt output.json/txt

(sequences.txt - lines of comma-separated integer IDs)

################################


To evaluate, run:

src/secret.py eval truemodel.json minedemodel.json 

################################


For more details and optional arguments, run:

src/secret.py --h

Sample parameters.json provided at data-shared/template.json

#################################


Notes:

Alphabet internally dealt as int (IDs of events) to allow arbitrarily large size and work with numpy arrays. Further, 0 and -1 not allowed as IDs.
Empty pattern (empty rule head) denoted as [-1]
