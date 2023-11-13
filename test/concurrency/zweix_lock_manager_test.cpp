#include <chrono>  // NOLINT
#include <random>  // NOLINT
#include <thread>  // NOLINT

#include "common/bustub_instance.h"
#include "common/config.h"
#include "common/util/string_util.h"
#include "concurrency/lock_manager.h"
#include "concurrency/transaction.h"
#include "concurrency/transaction_manager.h"

#include "fmt/core.h"
#include "gtest/gtest.h"

#define TEST_TIMEOUT_BEGIN                           \
  std::promise<bool> promisedFinished;               \
  auto futureResult = promisedFinished.get_future(); \
                              std::thread([](std::promise<bool>& finished) {
#define TEST_TIMEOUT_FAIL_END(X)                                                                  \
  finished.set_value(true);                                                                       \
  }, std::ref(promisedFinished)).detach();                                                        \
  EXPECT_TRUE(futureResult.wait_for(std::chrono::milliseconds(X)) != std::future_status::timeout) \
      << "Test Failed Due to Time Out";

namespace bustub {

TEST(LockManagerTest, AbortTest) {
  LockManager lock_mgr{};
  TransactionManager txn_mgr{&lock_mgr};

  auto bustub = std::make_unique<bustub::BustubInstance>();

  {
    std::cout << "Init: create a table named data.\n";
    std::stringstream ss;
    auto writer = bustub::SimpleStreamWriter(ss, true, " ");
    const std::string sql = "CREATE TABLE data(value int);";
    bustub->ExecuteSql(sql, writer);
    std::cout << ss.str() << "\n";
  }
  {
    std::cout << "check init.\n";
    std::stringstream ss;
    auto writer = bustub::SimpleStreamWriter(ss, true, " ");
    const std::string sql = "SELECT * FROM data;";
    bustub->ExecuteSql(sql, writer);
    std::cout << ss.str() << "\n";
    EXPECT_EQ(ss.str(), "");
  }
  {
    std::cout << "test: use a txn to insert and abort.\n";
    std::stringstream ss;
    auto writer = bustub::SimpleStreamWriter(ss, true, " ");
    const std::string sql = "INSERT INTO data VALUES (1);";
    auto txn = bustub->txn_manager_->Begin(nullptr, bustub::IsolationLevel::READ_UNCOMMITTED);
    bustub->ExecuteSqlTxn(sql, writer, txn);
    bustub->txn_manager_->Abort(txn);
    delete txn;
  }
  {
    std::cout << "check: the table have nothing.\n";
    std::stringstream ss;
    auto writer = bustub::SimpleStreamWriter(ss, true, " ");
    const std::string sql = "SELECT * FROM data;";
    bustub->ExecuteSql(sql, writer);
    std::cout << ss.str() << "\n";
    EXPECT_EQ(ss.str(), "");
  }
}

TEST(LockManagerTest, TerrierTest) {
  LockManager lock_mgr{};
  TransactionManager txn_mgr{&lock_mgr};

  auto bustub = std::make_unique<bustub::BustubInstance>();
}

TEST(LockManagerTest, TTest) {
  const int num = 5;
  LockManager lock_mgr{};
  TransactionManager txn_mgr{&lock_mgr};

  auto bustub = std::make_unique<bustub::BustubInstance>();

  {
    std::stringstream result;
    auto writer = bustub::SimpleStreamWriter(result, true, " ");
    auto sql = "CREATE TABLE ttest (x int, y int);";
    bustub->ExecuteSql(sql, writer);
    fmt::print("create table, sql = {}, ouput is \n{}\n", sql, result.str());
  }
  {
    std::stringstream result;
    auto writer = bustub::SimpleStreamWriter(result, true, " ");
    std::string sql = "INSERT INTO ttest VALUES ";
    for (size_t i = 0; i < num; i++) {
      sql += fmt::format("({}, {})", i, 0);
      if (i != num - 1) {
        sql += ", ";
      } else {
        sql += ";";
      }
    }
    bustub->ExecuteSql(sql, writer);
    fmt::print("insert, sql = {}, ouput is \n{}\n", sql, result.str());
  }
  {
    std::stringstream result;
    auto writer = bustub::SimpleStreamWriter(result, true, " ");
    auto sql = "select * from ttest;";
    bustub->ExecuteSql(sql, writer);
    fmt::print("select*, sql = {}, ouput is \n{}\n", sql, result.str());
  }

  for (int i = 1; i <= 10; ++i) {
    auto txn1 = bustub->txn_manager_->Begin();
    auto txn2 = bustub->txn_manager_->Begin();

    auto t2 = std::thread([txn2, &bustub] {
      std::string sql;
      std::stringstream result;
      auto writer = bustub::SimpleStreamWriter(result, true, " ");

      sql = "delete from ttest where x = 1;";
      bustub->ExecuteSqlTxn(sql, writer, txn2);
      result.str("");

      // fmt::print("{}\n", txn2->ToRepr());

      sql = "insert into ttest values (1, 100);";
      bustub->ExecuteSqlTxn(sql, writer, txn2);
      result.str("");

      // fmt::print("{}\n", txn2->ToRepr());

      bustub->txn_manager_->Commit(txn2);
    });

    auto t1 = std::thread([txn1, &bustub, num] {
      // std::this_thread::sleep_for(std::chrono::milliseconds(30));
      std::string sql;
      std::stringstream result;
      auto writer = bustub::SimpleStreamWriter(result, true, " ");

      sql = "select * from ttest;";
      bustub->ExecuteSqlTxn(sql, writer, txn1);

      bustub->txn_manager_->Commit(txn1);

      auto str = result.str();
      auto t = StringUtil::Split(str, "\n");

      EXPECT_EQ(t.size(), num);
    });

    t1.join();
    t2.join();

    delete txn1;
    delete txn2;
  }
}

}  // namespace bustub
