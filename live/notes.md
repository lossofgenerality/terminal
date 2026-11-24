# Packing Station (live) — Production notes

*Made from the CCN Terminal template · 2026-11-24 UTC · page design build 2026.11.24-0415*

## Jobs

None are written into the page: the Job menu comes from the service at sign-in (the jobs saved in the authoring tool), and each job's specifics and sub-tasks are fetched from the service when it is chosen.

## Sign-in and sign-out

- The passkey is checked by the service at https://www.wolframcloud.com/obj/ccn2/TerminalKernel.
- Every tick, untick and click is reported at once; with no connection they wait under *Waiting to send*, and sign-out completes only once the service has them all.

© Computational Classnotes · CC BY-NC-SA 4.0
