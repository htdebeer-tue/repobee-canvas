"""Use RepoBee with a Canvas assignment"""
import os
from pathlib import Path
import tempfile
import shutil

import repobee_plug as plug

# Other repobee-canvas commands:
from .command.create_canvas_git_mapping import CreateCanvasGitMapping
from .command.create_students_file      import CreateStudentsFile
from .command.init_assignment           import InitAssignment
from .command.init_course               import InitCourse
from .command.prepare_canvas_assignment import PrepareCanvasAssignment
from .command.send_message              import SendMessage

from .canvas_api.api                    import CanvasAPI
from .canvas_api.assignment             import Assignment
from .canvas_git_map                    import CanvasGitMap

from .common_options                    import CANVAS_ACCESS_TOKEN_OPTION
from .common_options                    import CANVAS_API_BASE_URL_OPTION
from .common_options                    import CANVAS_COURSE_ID_OPTION
from .common_options                    import CANVAS_ASSIGNMENT_ID_OPTION
from .common_options                    import CANVAS_ZIP_NAME_OPTION
from .common_options                    import CANVAS_UPLOAD_ZIP_OPTION
from .common_options                    import CANVAS_GIT_MAP_OPTION

from .tui                               import inform, warn, fault

URL_SUBMISSION = "online_url"


class Canvas(plug.Plugin, plug.cli.CommandExtension):
    """RepoBee-Canvas plugin.

    Canvas is a RepoBee plugin to handle creating, managing, and cloning student
    repositories based on the information from a Canvas assignment. Due to
    limitations of RepoBee, the students file with students assigned to the
    assignment has to be generated separately. Use the CanvasStudentsFile plugin
    for that (see above).
    """

    __settings__ = plug.cli.command_extension_settings(
            actions=[
                plug.cli.CoreCommand.repos.clone,
                plug.cli.CoreCommand.repos.setup,
                ]
            )

    canvas_access_token     = CANVAS_ACCESS_TOKEN_OPTION
    canvas_base_url         = CANVAS_API_BASE_URL_OPTION
    canvas_course_id        = CANVAS_COURSE_ID_OPTION
    canvas_assignment_id    = CANVAS_ASSIGNMENT_ID_OPTION
    canvas_upload_zip       = CANVAS_UPLOAD_ZIP_OPTION
    canvas_zip_name         = CANVAS_ZIP_NAME_OPTION
    canvas_git_map          = CANVAS_GIT_MAP_OPTION


    def post_setup(self, repo, api, newly_created):
        """Inform students about setup of their repository.

        After first creating a student repository, a message is posted to
        their assignment submission in Canvas. When the RepoBee `repos setup`
        command is run more than once, for example because some students did
        not yet have an account on Git, no message is posted.
        """
        try:
            canvas_git_mapping_table = CanvasGitMap.load(Path(self.canvas_git_map))

            students = [
                        canvas_git_mapping_table.git2canvas(member_id)
                        for member_id in repo.team.members
                       ]
            students_str = ", ".join(students)

            url = repo.url

            if not newly_created:
                inform((f"Re-run setup for: {students_str}. Gitlab URL "
                        f" ({url}) already published in Canvas"))
            else:
                inform((f"Publishing gitlab URL ({url}) to Canvas for: "
                        f" {students_str}."))

                CanvasAPI().setup(self.canvas_base_url, self.canvas_access_token)
                assignment = Assignment.load(self.canvas_course_id, self.canvas_assignment_id)

                try:
                    # Send comment to students' submission about their newly
                    # created repository.
                    submission = assignment.get_submission(students)

                    try:
                        submission.add_comment(f"Your project URL: {url}")

                    except ValueError as error:
                        fault("Unable to post URL as a comment. Reason: ", error)

                except ValueError as error:
                    warn((f"Unable to find submission related to "
                          f"repository '{url}' for '{students_str}'"), error)

        except ValueError as error:
            fault("Issue mapping student's Git ID to Canvas ID: ", error)


    def post_clone(self, repo, api):
        """Clone, zip, and submit students' work to the Canvas assignment.
        """
        if self.canvas_upload_zip:
            if not self.canvas_zip_name:
                raise ValueError(("When using '--canvas-upload-zip', you also"
                                  " need to specify a ZIP name with "
                                  "'--canvas-zip-name NAME'."))

            try:
                canvas_git_mapping_table = CanvasGitMap.load(Path(self.canvas_git_map))
                students = [
                            canvas_git_mapping_table.git2canvas(member_id)
                            for member_id in repo.team.members
                           ]
                students_str = ", ".join(students)

                # Name and base directory
                zip_name        = self.canvas_zip_name
                repo_base_dir   = tempfile.mkdtemp()
                repo_dir        = Path(repo_base_dir, zip_name)
                shutil.copytree(repo.path, str(repo_dir))

                # Zip the repo
                zip_base_dir    = tempfile.mkdtemp()
                zip_base_path   = Path(zip_base_dir, zip_name)
                zip_file_name   = f"{zip_name}.zip"
                zip_file_path   = f"{str(zip_base_path)}.zip"
                shutil.make_archive(str(zip_base_path), "zip", repo_base_dir, zip_name)

                inform((f"Submit zipped cloned gitlab repo as "
                        f"'{zip_file_name}' to Canvas for: {students_str}."))

                # Upload the ZIP file
                CanvasAPI().setup(self.canvas_base_url, self.canvas_access_token)
                assignment = Assignment.load(self.canvas_course_id, self.canvas_assignment_id)

                try:
                    submission = assignment.get_submission(students)

                    try:
                        submission.submit_file(zip_file_path)

                    except ValueError as error:
                        warn(("Unable to submit ZIP file. Attempt fall-back "
                              "to post it as a comment. Reason: "), error)

                        # There can be many reasons for failing tu submit or
                        # upload, although some rights issue might be
                        # at play. As a fallback, we send the URL as a comment to the
                        # submission, which will often succeed for these type of rights issues.
                        try:
                            submission.add_comment("Zipped cloned gitlab repo: ",
                                    zip_file_path)

                        except ValueError as error:
                            fault(("Unable to attach zipped cloned gitlab "
                                   "repo to a comment. Reason: "), error)

                except ValueError as error:
                    fault((f"Unable to find submission related to repository "
                           f"'{repo.url}' for '{students_str}'"), error)

                # Cleanup: removing all created directories
                shutil.rmtree(repo_base_dir)
                shutil.rmtree(zip_base_dir)

            except ValueError as error:
                fault("Error reading or using Canvas ID to Git ID map: ", error)
