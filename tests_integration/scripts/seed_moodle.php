<?php
define('CLI_SCRIPT', true);
require(__DIR__ . '/../config.php');
require_once($CFG->libdir . '/clilib.php');
require_once($CFG->libdir . '/grouplib.php');
require_once($CFG->dirroot . '/course/lib.php');
require_once($CFG->dirroot . '/user/lib.php');
require_once($CFG->dirroot . '/enrol/externallib.php');
require_once($CFG->libdir . '/gradelib.php');
require_once($CFG->dirroot . '/grade/querylib.php');

error_reporting(E_ALL);
ini_set('display_errors', '1');

// 1. Configure local_suap
set_config('token', 'test_token', 'local_suap');
set_config('auth_token', 'test_token', 'local_suap');
set_config('notes_to_sync', "'N1', 'N2', 'N3', 'N4', 'NAF'", 'local_suap');
set_config('noemailever', 1);

// 2. Format idnumber exactly like Integrador does
$diario_id = 'INT' . time();
$turma_codigo = '2025.3.18.1234';
$componente_sigla = 'MIC.AMB';
$course_idnumber = "{$turma_codigo}.{$componente_sigla}#{$diario_id}";

$category = $DB->get_record('course_categories', array('idnumber' => 'INTTEST'));
if (!$category) {
    $category = core_course_category::create(['name' => 'Integração Teste', 'idnumber' => 'INTTEST']);
}

$course_data = new stdClass();
$course_data->fullname = 'Curso de Teste Integração ' . $diario_id;
$course_data->shortname = 'INT' . $diario_id;
$course_data->category = $category->id;
$course_data->idnumber = $course_idnumber;
$course = create_course($course_data);
echo "DIARIO_ID: {$diario_id}\n";

// 3. Create fresh student
$username = 'std' . time();
$user_student = create_user_record($username, 'password123', 'manual');
$user_student->firstname = 'Aluno';
$user_student->lastname = 'Teste';
$user_student->email = $username . '@example.com';
$user_student->confirmed = 1;
$DB->update_record('user', $user_student);
echo "STUDENT_USERNAME: {$username}\n";

// 4. Enroll
$enrol = enrol_get_plugin('manual');
$instance = $DB->get_record('enrol', array('courseid' => $course->id, 'enrol' => 'manual'));
if (!$instance) {
    $enrol->add_instance($course);
    $instance = $DB->get_record('enrol', array('courseid' => $course->id, 'enrol' => 'manual'), '*', MUST_EXIST);
}
$student_role = $DB->get_record('role', array('shortname' => 'student'), '*', MUST_EXIST);
$enrol->enrol_user($instance, $user_student->id, $student_role->id);

// 5. Grades
$params = array(
    'courseid' => $course->id,
    'itemname' => 'Nota 1',
    'idnumber' => 'N1',
    'gradetype' => GRADE_TYPE_VALUE,
    'grademax' => 100,
    'itemtype' => 'manual'
);
$grade_item = new grade_item($params);
$grade_item->insert();
$grade_item->update_final_grade($user_student->id, 85.0);
grade_regrade_final_grades($course->id);

$seed_data = [
    'diario_id' => $diario_id,
    'student_username' => $username,
    'course_id' => $course->id
];
file_put_contents(__DIR__ . '/seed_data.json', json_encode($seed_data));

echo "Seed finalizado com sucesso.\n";
