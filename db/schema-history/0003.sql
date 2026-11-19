--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6 (Debian 18.6-1.pgdg13+2)
-- Dumped by pg_dump version 18.6 (Debian 18.6-1.pgdg13+2)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: educational_programs_guard(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.educational_programs_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM grades g JOIN study_plans p ON p.id = g.plan_id
               WHERE p.program_id = OLD.id AND g.record_status = 'зафиксирован') THEN
        RAISE EXCEPTION USING MESSAGE =
            'По программе есть зафиксированные результаты. '
            'Создайте новую версию программы (revision_no)';
    END IF;
    IF EXISTS (SELECT 1 FROM study_plans
               WHERE program_id = OLD.id AND semester > NEW.semester_count) THEN
        RAISE EXCEPTION USING MESSAGE =
            'В учебном плане программы есть дисциплины в семестрах после '
            || NEW.semester_count;
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: grades_guard(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.grades_guard() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    plan_form       VARCHAR(15);
    plan_program    INTEGER;
    student_program INTEGER;
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') AND OLD.record_status = 'зафиксирован' THEN
        RAISE EXCEPTION USING MESSAGE =
            'Запись зафиксирована (ведомость закрыта) и не может изменяться';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;

    SELECT report_form, program_id INTO plan_form, plan_program
    FROM study_plans WHERE id = NEW.plan_id;
    SELECT g.program_id INTO student_program
    FROM students s JOIN student_groups g ON g.id = s.group_id
    WHERE s.id = NEW.student_id;

    IF plan_program IS DISTINCT FROM student_program THEN
        RAISE EXCEPTION USING MESSAGE = 'Дисциплина не входит в учебный план студента';
    END IF;
    IF NEW.grade <> 'не явился'
       AND (plan_form = 'зачёт') <> (NEW.grade IN ('зачтено', 'не зачтено')) THEN
        RAISE EXCEPTION USING MESSAGE =
            'Оценка «' || NEW.grade || '» не подходит для формы «' || plan_form || '»';
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: study_plans_check_semester(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.study_plans_check_semester() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    max_semester SMALLINT;
BEGIN
    SELECT semester_count INTO max_semester
    FROM educational_programs WHERE id = NEW.program_id;
    IF NEW.semester > max_semester THEN
        RAISE EXCEPTION USING MESSAGE =
            'Семестр ' || NEW.semester || ' выходит за пределы программы (семестров: '
            || max_semester || ')';
    END IF;
    RETURN NEW;
END;
$$;


--
-- Name: study_plans_protect_fixed(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.study_plans_protect_fixed() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM grades
               WHERE plan_id = OLD.id AND record_status = 'зафиксирован') THEN
        RAISE EXCEPTION USING MESSAGE =
            'По этой строке плана есть зафиксированные результаты. '
            'Создайте новую версию программы (revision_no)';
    END IF;
    RETURN NEW;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: educational_programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.educational_programs (
    id integer NOT NULL,
    direction_code character(8) NOT NULL,
    profile character varying(150) NOT NULL,
    cohort_year smallint NOT NULL,
    study_form character varying(12) NOT NULL,
    revision_no smallint NOT NULL,
    semester_count smallint NOT NULL,
    CONSTRAINT educational_programs_code_ck CHECK ((direction_code ~ '^[0-9]{2}\.0[345]\.[0-9]{2}$'::text)),
    CONSTRAINT educational_programs_form_ck CHECK (((study_form)::text = ANY ((ARRAY['очная'::character varying, 'очно-заочная'::character varying, 'заочная'::character varying])::text[]))),
    CONSTRAINT educational_programs_profile_ck CHECK ((btrim((profile)::text) <> ''::text)),
    CONSTRAINT educational_programs_revision_ck CHECK ((revision_no > 0)),
    CONSTRAINT educational_programs_semesters_ck CHECK (((semester_count >= 1) AND (semester_count <= 14))),
    CONSTRAINT educational_programs_year_ck CHECK ((cohort_year >= 2016))
);


--
-- Name: educational_programs_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.educational_programs ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.educational_programs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: grades; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.grades (
    id integer NOT NULL,
    student_id integer NOT NULL,
    plan_id integer NOT NULL,
    attempt_no smallint NOT NULL,
    assessed_on date NOT NULL,
    grade character varying(10) NOT NULL,
    basis_ref character varying(64) NOT NULL,
    record_status character varying(12) NOT NULL,
    CONSTRAINT grades_attempt_ck CHECK ((attempt_no = ANY (ARRAY[1, 2, 3]))),
    CONSTRAINT grades_basis_ck CHECK ((btrim((basis_ref)::text) <> ''::text)),
    CONSTRAINT grades_grade_ck CHECK (((grade)::text = ANY ((ARRAY['2'::character varying, '3'::character varying, '4'::character varying, '5'::character varying, 'зачтено'::character varying, 'не зачтено'::character varying, 'не явился'::character varying])::text[]))),
    CONSTRAINT grades_status_ck CHECK (((record_status)::text = ANY ((ARRAY['черновик'::character varying, 'зафиксирован'::character varying])::text[])))
);


--
-- Name: grades_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.grades ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.grades_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: student_groups; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_groups (
    id integer NOT NULL,
    group_name character varying(8) NOT NULL,
    program_id integer NOT NULL,
    CONSTRAINT student_groups_name_ck CHECK (((group_name)::text ~ '^[0-9]{3}-[0-9]{3,4}$'::text))
);


--
-- Name: student_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.student_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.student_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: students; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.students (
    id integer NOT NULL,
    last_name character varying(60) NOT NULL,
    first_name character varying(60) NOT NULL,
    patronymic character varying(60),
    student_no character varying(10) NOT NULL,
    admission_year smallint NOT NULL,
    group_id integer NOT NULL,
    status character varying(30) NOT NULL,
    academic_note character varying(120),
    CONSTRAINT students_first_name_ck CHECK ((btrim((first_name)::text) <> ''::text)),
    CONSTRAINT students_last_name_ck CHECK ((btrim((last_name)::text) <> ''::text)),
    CONSTRAINT students_no_ck CHECK (((student_no)::text ~ '^[0-9]{1,10}$'::text)),
    CONSTRAINT students_status_ck CHECK (((status)::text = ANY ((ARRAY['обучается'::character varying, 'академический отпуск'::character varying, 'отпуск по беременности и родам'::character varying, 'отпуск по уходу за ребёнком'::character varying, 'отчислен'::character varying, 'выпускник'::character varying])::text[]))),
    CONSTRAINT students_year_ck CHECK ((admission_year >= 2016))
);


--
-- Name: students_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.students ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.students_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: study_plans; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.study_plans (
    id integer NOT NULL,
    program_id integer NOT NULL,
    discipline character varying(150) NOT NULL,
    semester smallint NOT NULL,
    hours smallint NOT NULL,
    report_form character varying(15) NOT NULL,
    CONSTRAINT study_plans_discipline_ck CHECK ((btrim((discipline)::text) <> ''::text)),
    CONSTRAINT study_plans_form_ck CHECK (((report_form)::text = ANY ((ARRAY['экзамен'::character varying, 'зачёт'::character varying, 'зачёт с оценкой'::character varying])::text[]))),
    CONSTRAINT study_plans_hours_ck CHECK ((hours > 0)),
    CONSTRAINT study_plans_semester_ck CHECK ((semester >= 1))
);


--
-- Name: study_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.study_plans ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.study_plans_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: educational_programs educational_programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_programs
    ADD CONSTRAINT educational_programs_pkey PRIMARY KEY (id);


--
-- Name: educational_programs educational_programs_version_uq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.educational_programs
    ADD CONSTRAINT educational_programs_version_uq UNIQUE (direction_code, profile, cohort_year, study_form, revision_no);


--
-- Name: grades grades_event_uq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grades
    ADD CONSTRAINT grades_event_uq UNIQUE (student_id, plan_id, attempt_no, assessed_on);


--
-- Name: grades grades_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grades
    ADD CONSTRAINT grades_pkey PRIMARY KEY (id);


--
-- Name: student_groups student_groups_name_uq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_groups
    ADD CONSTRAINT student_groups_name_uq UNIQUE (group_name);


--
-- Name: student_groups student_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_groups
    ADD CONSTRAINT student_groups_pkey PRIMARY KEY (id);


--
-- Name: students students_no_uq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_no_uq UNIQUE (student_no);


--
-- Name: students students_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_pkey PRIMARY KEY (id);


--
-- Name: study_plans study_plans_component_uq; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_component_uq UNIQUE (program_id, discipline, semester);


--
-- Name: study_plans study_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_pkey PRIMARY KEY (id);


--
-- Name: educational_programs_form_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX educational_programs_form_idx ON public.educational_programs USING btree (study_form);


--
-- Name: grades_plan_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX grades_plan_idx ON public.grades USING btree (plan_id);


--
-- Name: grades_result_uq; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX grades_result_uq ON public.grades USING btree (student_id, plan_id, attempt_no) WHERE ((grade)::text <> 'не явился'::text);


--
-- Name: student_groups_program_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX student_groups_program_idx ON public.student_groups USING btree (program_id);


--
-- Name: students_group_status_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX students_group_status_idx ON public.students USING btree (group_id, status);


--
-- Name: study_plans_discipline_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX study_plans_discipline_idx ON public.study_plans USING btree (discipline);


--
-- Name: educational_programs educational_programs_guard_trg; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER educational_programs_guard_trg BEFORE UPDATE ON public.educational_programs FOR EACH ROW EXECUTE FUNCTION public.educational_programs_guard();


--
-- Name: grades grades_guard_trg; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER grades_guard_trg BEFORE INSERT OR DELETE OR UPDATE ON public.grades FOR EACH ROW EXECUTE FUNCTION public.grades_guard();


--
-- Name: study_plans study_plans_protect_trg; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER study_plans_protect_trg BEFORE UPDATE ON public.study_plans FOR EACH ROW EXECUTE FUNCTION public.study_plans_protect_fixed();


--
-- Name: study_plans study_plans_semester_trg; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER study_plans_semester_trg BEFORE INSERT OR UPDATE ON public.study_plans FOR EACH ROW EXECUTE FUNCTION public.study_plans_check_semester();


--
-- Name: grades grades_plan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grades
    ADD CONSTRAINT grades_plan_id_fkey FOREIGN KEY (plan_id) REFERENCES public.study_plans(id) ON DELETE RESTRICT;


--
-- Name: grades grades_student_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.grades
    ADD CONSTRAINT grades_student_id_fkey FOREIGN KEY (student_id) REFERENCES public.students(id) ON DELETE RESTRICT;


--
-- Name: student_groups student_groups_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_groups
    ADD CONSTRAINT student_groups_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.educational_programs(id) ON DELETE RESTRICT;


--
-- Name: students students_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.students
    ADD CONSTRAINT students_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.student_groups(id) ON DELETE RESTRICT;


--
-- Name: study_plans study_plans_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.study_plans
    ADD CONSTRAINT study_plans_program_id_fkey FOREIGN KEY (program_id) REFERENCES public.educational_programs(id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--


