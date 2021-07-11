import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    @app.after_request
    def after_request(responce):
        responce.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        responce.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return responce

    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE
        questions = [question.format() for question in selection]
        questions_current = questions[start:end]
        return questions_current

    @app.route('/categories', methods=['GET'])
    def categories_get_all():
        categories = Category.query.all()
        if not categories:
            abort(404)

        return jsonify({
            'success': True,
            'categories': {category.id: category.type
                           for category in categories
                           }
        })

    @app.route('/questions')
    def questions_get_list():
        questions_selection = Question.query.order_by(Question.id).all()
        questions = paginate_questions(request, questions_selection)
        categories = Category.query.all()

        if not questions:
            abort(404)

        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(questions_selection),
            'current_category': None,
            'categories': {
                category.id: category.type
                for category in categories
            },
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def question_delete_id(question_id):

        question_with_id = Question.query.filter(Question.id == question_id).one_or_none()

        if question_with_id is None:
            abort(404)

        try:
            question_with_id.delete()

            return jsonify({
                'success': True,
                'deleted': question_id
            })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def create_new_question():
        question_body = request.get_json()

        new_question = question_body.get('question')
        new_answer = question_body.get('answer')
        new_category = question_body.get('category')
        new_difficulty = question_body.get('difficulty')

        if new_question == '' or new_answer == '' or new_category == '' or new_difficulty == '':
            abort(400)

        try:
            question_add = Question(question=new_question, answer=new_answer,
                                    category=new_category, difficulty=new_difficulty)
            question_add.insert()

            return jsonify({
                'success': True,
                'created': question_add.id
            })
        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def questions_search():
        search_body = request.get_json()
        search_term = search_body.get('searchTerm')
        search_question = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
        if not search_question:
            abort(404)

        paginate_search = paginate_questions(request, search_question)

        return jsonify({
            'success': True,
            'questions': paginate_search,
            'total_questions': len(Question.query.all()),
            'current_category': None
        })

    @app.route('/categories/<int:id>/questions', methods=['GET'])
    def choose_category_of_questions(id):
        try:
            category_questions = Question.query.filter(Question.category == str(id)).all()
            paginate_category = paginate_questions(request, category_questions)

            return jsonify({
                'success': True,
                'questions': paginate_category,
                'total_questions': len(category_questions),
                'current_category': id
            })
        except:
            abort(404)

    @app.route('/quizzes', methods=['POST'])
    def quizzes():
        quiz_body = request.get_json()
        questions_previous = quiz_body.get('previous_questions')
        category_quiz = quiz_body.get('quiz_category')
        try:
            quiz_id = category_quiz['id']

            if not quiz_id:
                query_questions = Question.query.filter(Question.id.notin_(questions_previous)).all()
            else:
                query_questions = Question.query.filter(Question.category == category_quiz['id']). \
                    filter(Question.id.notin_(questions_previous)).all()

            if query_questions:
                next_question = random.choice(query_questions)
            else:
                return jsonify({
                    'success': True,
                    'question': None
                })

            return jsonify({
                'success': True,
                'question': next_question.format()
            })
        except:
            abort(422)

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'internal server error'
        }), 500

    @app.errorhandler(404)
    def resource_not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        }), 400

    return app
