# Example: Staged Workflow

1. `tosea_parse_pdf`
2. `tosea_wait_for_job`
3. `tosea_generate_outline`
4. `tosea_wait_for_job`
5. `tosea_edit_outline_page`
6. `tosea_render_slides`
7. `tosea_wait_for_job`
8. `tosea_edit_slide_page`
9. `tosea_export_presentation`
10. `tosea_wait_for_job`
11. Optional: `tosea_list_export_files`

Use this path when the user asks for outline changes, inserted slides, or iteration after review.

