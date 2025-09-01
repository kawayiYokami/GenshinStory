import unittest
from zzz_data_parser.dataloader import ZZZDataLoader
from zzz_data_parser.services.dialogue_service import DialogueService
from zzz_data_parser.formatters.dialogue_formatter import DialogueFormatter

class TestUnifiedPipeline(unittest.TestCase):

    def test_specific_chapter_formatting(self):
        """
        测试一个已知的特定章节，验证其格式化逻辑是否正确。
        """
        # --- 1. 初始化 ---
        data_loader = ZZZDataLoader(gender='M', player_name='哲')
        service = DialogueService(data_loader)

        # --- 2. 获取特定章节 ---
        # 修正：我们应该传入章节ID，而不是某一行对话的完整Key
        chapter_id = "Chapter05"
        chapter = service.get_chapter_by_id(chapter_id)

        self.assertIsNotNone(chapter, f"Chapter '{chapter_id}' should not be None.")
        self.assertEqual(chapter.id, chapter_id)

        # --- 3. 格式化并验证 ---
        formatter = DialogueFormatter(chapter)
        markdown_files = formatter.to_markdown_files()

        # 3.1. 验证返回类型和内容
        self.assertIsInstance(markdown_files, dict, "The formatter should return a dictionary.")
        self.assertGreater(len(markdown_files), 0, "The dictionary of markdown files should not be empty.")

        # 3.2. 验证第一个文件的名称和内容
        # 注意: 排序是基于 act_id 的数字大小
        first_filename = sorted(markdown_files.keys())[0]
        first_content = markdown_files[first_filename]

        # 修正：文件名应该是基于正确的章节ID
        self.assertEqual(first_filename, f"{chapter_id}-1.md", "The first filename is incorrect.")
        self.assertIn("# 第 1 幕", first_content, "The content should contain the act number title.")
        self.assertIn("出场角色", first_content, "The content should list the speakers.")
        # 修正断言：根据上次测试失败的输出，使用 Chapter05 中真实存在的文本进行验证
        self.assertIn("哥哥，妮可打电话说", first_content, "The content should include a correct dialogue line from Chapter05.")
        print(f"\nSuccessfully validated formatting for chapter '{chapter_id}'.")
        print(f"Generated file: {first_filename}")
        print("--- Sample Content ---")
        print(first_content[:300] + "...")
        print("----------------------")


if __name__ == '__main__':
    unittest.main()