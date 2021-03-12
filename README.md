# repobee-canvas

Repobee-canvas is a plugin for [RepoBee](https://github.com/repobee/repobee) to manage student git repositories using information from a 
[Canvas](https://www.instructure.com/canvas) assignment. With repobee-canvas,
you can upload and submit a ZIP file of a student's repository to preserve
their work in Canvas.

# Licence

Repobee-canvas is free software. Repobee-canvas is released under the [EUPL
1.2](https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12) or later.

# Usage

Install and setup RepoBee by following [RepoBee's
manual](https://docs.repobee.org/en/stable/index.html). 

## Configure repobee-canvas

1.  [Install](https://docs.repobee.org/en/stable/plugins.html#installing-plugins-the-install-action)
    the `repobee-canvas` plugin.
2.  Generate a Canvas API key via "Account", "Settings", "+ New Access Token".
3.  Get the Canvas course id.
4.  Configure RepoBee Canvas with `repobee -p canvas config wizard`. The `-p
    cnavas` enables the Canvas plugin. This command starts the configuration
    wizard. Choose the section "canvas". The wizard asks you to fill in:

    - `canvas_api_key`
    - `canvas_api_key` For example, "https://my.canvas.com/api/v1"
    - `canvas_course_id`
    - `canvas_start_assignment_message` Skip this field for now.

5.  Create a CSV file to map students' Canvas IDs to their git IDs. This
    CSV file should have at least two columns, one named
    `canvas_id`, and the other `git_id`. More columns are allowed, even
    recommended. For example, adding a `name` and `email` column makes looking
    up IDs manually much easier.

## Prepare and hand out the assignment

1.  Prepare the assignment by running the command `repobee -p canvas prepare-assignment
    --canvas-assignment-id XXX`. This command first checks that the Canvas
    assignment XXX allows file uploads. If so, the command sends a welcome message to all
    students participating in the assignment. 

    Sending a message to all students is needed to create a submission in
    Canvas for each student group participating in the assignment. Without
    this message, repobee-canvas cannot discover the students working in a group.

    Furthermore, by sending a message like the default message "This
    assignment is managed by repobee-canvas.", you are transparent about
    repobee-canvas managing this assignment.

    If you want to send a different message that the standard message, you can
    either configure this globally via the config wizard, or use the
    command-line option `--canvas-start-assignment-message`. *Note* You can
    also use this command to send messages to Canvas submissions.

2.  Generate the students file used by RepoBee. RepoBee uses the students file
    to create a GitHub team or GitLab suborganization for groups of students
    or individual student participating in an assignment, and then create a
    repository for this team or sub group. 

    Run the command `repobee -p canvas generate-students-file
    --canvas-assignment-id XXX --canvas-git-map YYY.csv
    --canvas-students-file ZZZ.lst`. This generates the file
    "ZZZ.lst" containing the git IDs for the students participating in the
    assignment using the database "YYY.csv".
    
3.  Generate the student repositories. Run command `repobee -p gitlab -p
    canvas repos setup --assignments AAA --students-file
    ZZZ.lst --canvas-assignment-id XXX --canvas-git-map
    YYY.csv`


## Running the assignment

I have not developed any Canvas specific functionality yes. Use RepoBee
standard functionality. I do plan to integrate with Canvas peer-review
functionality.

## Finishing  /  Clone + Upload assignment 

You can run `repobe repos clone` as usual. However, if you want to upload and
submit a ZIP file of the cloned student repository to Canvas, use command-line
parameters `--canvas-upload-zip` and `--canvas-zip-name NAME`. For example,
run `repobee -p gitlab -p canvas repos clone --assignments AAA
--students-file ZZZ.lst --canvas-assignment-id XXX --canvas-git-map
YYY.csv --canvas-upload-zip --canvas-zip-name NNN`. This will clone all
student repositories, zip each of the cloned repositories, and upload and
submit that ZIP file as "NNN.zip" to the Canvas assignment.


Note. I will write a complete manual later.

Repobee-canvas is still a work in progress. 