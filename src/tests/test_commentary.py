import unittest
from unittest.mock import patch, MagicMock
from src.Minerva.commentary import identify_comment_points, parse_points_and_questions, interact_with_questions, generate_comments, generate_general_comment, insert_general_comment, review_comments

class TestCommentary(unittest.TestCase):
    def test_identify_comment_points(self):
        # test implementation
        pass

    def test_parse_points_and_questions(self):
        response = """**Fragment 1**  
*"Muy linda la clase"*  
¿Qué específicamente hizo que la clase fuera “muy linda” para ti?  

---

**Fragment 2**  
*"No se si puedo seguir yendo sin estudiar"*  
¿Qué específicamente te genera dudas sobre continuar con las clases sin estudiar?  

---

**Fragment 3**  
*"El camino de vuelta se hizo muy muy pesado"*  
¿Qué específicamente hizo que el camino de vuelta fuera tan pesado para ti?  

---

**Fragment 4**  
*"Muy bueno jugar después de tanto tiempo"*  
¿Qué específicamente hizo que jugar fuese “muy bueno” para ti después de tanto tiempo?  

---

**Fragment 5**  
*"Jugué muy bien, soy buen Defensor"*  
¿Qué específicamente te hizo sentir que jugaste muy bien y tuviste buena defensa?  

---

**Fragment 6**  
*"Ana estaba muy caída"*  
¿Qué signos específicos notaste que indicaron que Ana estaba muy caída?  

---

**Fragment 7**  
*"Estaba muy cansado cuando llegue"*  
¿Qué específicamente hizo que te sentieras tan cansado cuando llegaste?"""
        points, questions = parse_points_and_questions(response)
        self.assertIsNotNone(points)
        self.assertIsNotNone(questions)

    def test_interact_with_questions(self):
        # test implementation
        pass

    def test_generate_comments(self):
        # test implementation
        pass

    def test_generate_general_comment(self):
        # test implementation
        pass

    def test_insert_general_comment(self):
        # test implementation
        pass

    def test_review_comments(self):
        # test implementation
        pass

if __name__ == '__main__':
    unittest.main()
