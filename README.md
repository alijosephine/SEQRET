This repo contains code and data for [SEQRET: Mining Rule Sets from Event Sequences](https://eda.rg.cispa.io/prj/seqret/).

## Overview:
[SEQRET Poster](assets/SEQRET_AAAI26_poster.pdf)  
[SEQRET Slides](assets/SEQRET_AAAI26_slides.pdf)

## Usage:

### To generate data:
```bash
src/secret.py gen parameters.json
```
- The generated model and sequence will be written to destinations provided in `parameters.json`.
- An example `parameters.json` is provided at `data-shared/template.json`.

### To mine rules:
```bash
src/secret.py mine parameters.json sequences.txt output.json/txt
```
- Lines of comma-separated integer IDs to be provided in `sequences.txt`.
- An example `parameters.json` is provided at `data-shared/template.json`.

### To evaluate:
```bash
src/secret.py eval truemodel.json minedemodel.json 
```

### For more details and optional arguments:
```bash
src/secret.py --h
```

#### Notes:

1. Alphabet internally dealt as int (IDs of events) to allow arbitrarily large size and work with numpy arrays.
2. Further, 0 and -1 not allowed as IDs.
3. Empty pattern (empty rule head) denoted as [-1]


### To cite our work:

```bibtex
@inproceedings{seqret,
  title={SEQRET: Mining Rule Sets from Event Sequences},
  author={Siji, Aleena and Cüppers, Joscha and Mian, Osman and Vreeken, Jilles},
  booktitle={Proceedings of the AAAI Conference on Artificial Intelligence},
  volume={40},
  year={2026}
}
```
