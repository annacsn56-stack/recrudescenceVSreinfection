# hmmIBD (third-party software)

This directory contains **hmmIBD**, a program that infers pairwise identity by
descent (IBD) between haploid genotypes. **hmmIBD is not part of this study's
own code**: it was developed and is maintained by S. F. Schaffner and
colleagues, and is included here only to document the exact version used in our
analyses and to facilitate reproduction.

## Source

- **Publication:** Schaffner, S.F., Taylor, A.R., Wong, W. et al. hmmIBD:
  software to infer pairwise identity by descent between haploid genotypes.
  *Malar J* 17, 196 (2018). https://doi.org/10.1186/s12936-018-2349-7
- **Repository:** https://github.com/glipsnort/hmmIBD

## Version used in this study

- Version / release: `2.0.0`   <!-- à compléter -->

## License

hmmIBD is distributed under the terms of its **original license**, as provided
in the upstream repository. That license — not the license of this study's
repository — governs the files in this directory. Please refer to the upstream
repository for the authoritative license text.

## How it is used here

hmmIBD was run on VCFs converted to the hmmIBD input format (see
`../scripts/vcf2hmm.py`), producing the pairwise `fract_sites_IBD` values used for the
relatedness and clustering analyses. See the main project README for the full
pipeline and for how to regenerate the IBD results.

## Citation

If you use hmmIBD, please cite the publication above.
